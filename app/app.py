import json
import shutil
import zipfile
from pathlib import Path

import rdflib
from cloudevents.events import (
    CEMessageMode,
    Event,
    EventAttributes,
    EventOutcome,
    PulsarBinding,
)
from viaa.configuration import ConfigParser
from viaa.observability import logging

from app.helpers import graph, xml

# from helpers.xml import build_mh_sidecar
from app.services.pid import PidClient
from app.services.pulsar import PulsarClient

APP_NAME = "mh-sip-creator"


class EventListener:
    def __init__(self):
        config_parser = ConfigParser()
        self.log = logging.get_logger(__name__, config=config_parser)
        self.config = config_parser.app_cfg
        self.pulsar_client = PulsarClient()
        self.pid_client = PidClient()

        # Topics
        self.app_config = self.config["mh-sip-creator"]
        self.consumer_topic = self.app_config["consumer_topic"]

    def produce_event(
        self,
        topic: str,
        data: dict,
        subject: str,
        outcome: EventOutcome,
        correlation_id: str,
    ):
        """Produce an event on a Pulsar topic.
        Args:
            topic: The topic to send the cloudevent to.
            data: The data payload.
            subject: The subject of the event.
            outcome: The attributes outcome of the Event.
            correlation_id: The correlation ID.
        """
        attributes = EventAttributes(
            type=topic,
            source=APP_NAME,
            subject=subject,
            correlation_id=correlation_id,
            outcome=outcome,
        )

        event = Event(attributes, data)
        self.pulsar_client.produce_event(topic, event)

    def handle_incoming_message(self, event: Event):
        """
        Handles an incoming pulsar event.
        """
        # If the event failed or the shacl validation failed we drop the event.
        if not event.has_successful_outcome():
            self.log.info(f"Dropping non succesful event: {event.get_data()}")
            return

        # Parse the incoming metadata as a graph.
        metadata_graph_format = event.get_data().get("metadata_graph_fmt", "")
        metadata_graph = graph.parse_graph(
            event.get_data()["metadata_graph"], metadata_graph_format
        )

        sip = graph.get_sip_info(metadata_graph)

        # Path to unzipped bag
        # `/opt/sipin/unzip/<name>.bag.zip`
        path: str = event.get_attributes()["subject"]
        pid = graph.get_pid_from_graph(metadata_graph)
        if not pid:
            pid = self.pid_client.get_pid()

        if (
            len(sip.representations) == 1
            and len(sip.representations[0].files) == 1
            and sip.profile == "basic"
        ):
            # We make essence + sidecar ready for tra
            cp_id = graph.get_cp_id_from_graph(metadata_graph)
            filename = Path(sip.representations[0].files[0].filename)
            md5 = sip.representations[0].files[0].fixity
            ie = metadata_graph.value(
                predicate=rdflib.URIRef(
                    "http://www.w3.org/1999/02/22-rdf-syntax-ns#type"
                ),
                object=rdflib.URIRef(
                    "http://www.loc.gov/premis/rdf/v3/IntellectualEntity"
                ),
            )
            sidecar = xml.build_mh_sidecar(metadata_graph, ie, pid, {"md5": md5})

            essence_filepath = Path(
                path, "data/representations/representation_1/data", filename
            )
            sidecar_filepath = Path(
                path, "data/representations/representation_1/data", filename
            ).with_suffix(".xml")

            # Write sidecar to file
            with open(sidecar_filepath, "w") as xml_file:
                xml_file.write(sidecar)

            # Move file(s) to AIP folder with PID as filename(s)
            aip_filepath = Path(self.app_config["aip_folder"], pid)

            shutil.move(
                essence_filepath,
                aip_filepath.with_suffix(filename.suffix),
            )
            shutil.move(sidecar_filepath, aip_filepath.with_suffix(".xml"))

            # Send event on topic
            data = {
                "source": path,
                "host": self.config["host"],
                "paths": [
                    str(aip_filepath.with_suffix(filename.suffix)),
                    str(aip_filepath.with_suffix(".xml")),
                ],
                "cp_id": cp_id,
                "type": "pair",
                "sip_profile": sip.profile,
                "pid": pid,
                "outcome": EventOutcome.SUCCESS,
                "message": f"AIP created: sidecar ingest for {filename}",
            }

            producer_topic = self.app_config["producer_topic_basic"]

            self.log.info(data["message"])
        else:
            if sip.profile == "material-artwork":
                # Make a folder that will be zipped as the complex.
                files_path = Path(self.app_config["aip_folder"], pid)
                files_path.mkdir()

                # Dump all files of the sip in the folder.
                for i in range(len(sip.representations)):
                    shutil.copytree(
                        Path(path, f"data/representations/representation_{i+1}/data"),
                        Path(files_path, f"representation_{i+1}"),
                        copy_function=shutil.move,
                    )

                # Generate mets xml
                mets_xml = xml.build_mh_mets(
                    metadata_graph, pid, self.app_config["archive_location"]
                )
                # Write xml to the complex folder
                with open(Path(files_path, "mets.xml"), "w") as mets_file:
                    mets_file.write(mets_xml)
                # Zip everything
                shutil.make_archive(str(Path(f"{files_path}")), "zip", files_path)
                # Remove files folder
                shutil.rmtree(files_path)

                cp_id = graph.get_cp_id_from_graph(metadata_graph)

                # Send event on topic
                data = {
                    "source": path,
                    "host": self.config["host"],
                    "paths": [
                        str(Path(f"{files_path}.zip")),
                    ],
                    "cp_id": cp_id,
                    "type": "complex",
                    "sip_profile": sip.profile,
                    "pid": pid,
                    "outcome": EventOutcome.SUCCESS,
                    "message": f"AIP created: MH2.0 complex created for {path}",
                }
                producer_topic = self.app_config["producer_topic_complex"]

                self.log.info(data["message"])
        self.produce_event(
            producer_topic, data, path, EventOutcome.SUCCESS, event.correlation_id
        )

    def main(self):
        while True:
            msg = self.pulsar_client.receive()
            try:
                event = PulsarBinding.from_protocol(msg)
                self.handle_incoming_message(event)
                self.pulsar_client.acknowledge(msg)
            except Exception as e:
                # Generic catch all remaining errors.
                self.log.error(f"Error: {e}")
                # Message failed to be processed
                self.pulsar_client.negative_acknowledge(msg)

        self.pulsar_client.close()
