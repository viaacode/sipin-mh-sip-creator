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

from app.mappings import material_artwork

APP_NAME = "mh-sip-creator"


class EventListener:
    def __init__(self):
        config_parser = ConfigParser()
        self.log = logging.get_logger(__name__, config=config_parser)
        self.config = config_parser.app_cfg
        self.pulsar_client = PulsarClient(APP_NAME)
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

        # `subject` contains the path to the unzipped bag.
        self.log.info(f"Start handling of {event.get_attributes()['subject']}.")

        # Parse the incoming metadata as a graph using the supplied format or json-ld as fallback.
        metadata_graph_format = event.get_data().get("metadata_graph_fmt", "")
        metadata_graph = graph.parse_graph(
            event.get_data()["metadata_graph"], metadata_graph_format
        )

        sip = graph.get_sip_info(metadata_graph)

        if not sip.profile in ["basic", "newspaper", "material-artwork"]:
            self.log.warn(f"No support for SIPs with {sip.profile} profile.")
            return

        # Path to unzipped bag
        # `/opt/sipin/unzip/<name>.bag.zip`
        path: str = event.get_attributes()["subject"]

        # In some cases a PID is supplied by the CP, if not, we generate a new one.
        pid = graph.get_pid_from_graph(metadata_graph)
        if not pid:
            pid = self.pid_client.get_pid()

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

        # Set the storage location based on CP id.
        cp_info = graph.get_cp_info_from_graph(metadata_graph)
        if cp_info:
            cp_id = cp_info.id
        else:
            cp_id = ""

        archive_location = self.app_config["storage"]["default_archive_location"]

        tape_content_partners = [
            or_id.strip().lower()
            for or_id in self.app_config["storage"]["tape_content_partners"].split(",")
        ]
        disk_content_partners = [
            or_id.strip().lower()
            for or_id in self.app_config["storage"]["disk_content_partners"].split(",")
        ]

        if cp_id.lower() in tape_content_partners:
            archive_location = "Tape"
        if cp_id.lower() in disk_content_partners:
            archive_location = "Disk"

        # Generate mets xml based on profile
        if sip.profile == "newspaper":
            mets_xml = xml.build_newspaper_mh_mets(
                metadata_graph,
                pid,
                archive_location,
                {
                    "dynamic": {"batch_id": sip.batch_id, "text_type": sip.format, "dc_format": "kranteneditie"},
                    "descriptive": {"OriginalFilename": Path(path).name},
                },
            )
        if sip.profile == "material-artwork":
            mets_xml = xml.build_mh_mets(
                metadata_graph,
                pid,
                archive_location,
                {
                    "dynamic": {"batch_id": sip.batch_id, "type_viaa": sip.format},
                    "descriptive": {"OriginalFilename": Path(path).name},
                },
            )

        if sip.profile == "basic":
            mets_xml = xml.build_basic_mh_mets(
                metadata_graph,
                pid,
                archive_location,
                {
                    "dynamic": {"batch_id": sip.batch_id, "type_viaa": sip.format},
                    "descriptive": {"OriginalFilename": Path(path).name},
                },
            )
        if sip.profile == "bibliographic":
            mets_xml = xml.build_bibliographic_mh_mets(
                metadata_graph,
                pid,
                self.app_config["archive_location"],
                {
                    "dynamic": {"batch_id": sip.batch_id, "text_type": sip.format},
                    "descriptive": {"OriginalFilename": Path(path).name},
                },
            )

        # Write xml to the complex folder
        with open(Path(files_path, "mets.xml"), "w") as mets_file:
            mets_file.write(mets_xml)
        # Zip everything
        with zipfile.ZipFile(str(Path(f"{files_path}.zip")), "w") as zf:
            for file_path in files_path.rglob("*"):
                zf.write(file_path, arcname=file_path.relative_to(files_path))
        # Remove files folder
        shutil.rmtree(files_path)

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
            "metadata": mets_xml,
            "message": f"AIP created: MH2.0 complex created for {path}",
        }
        producer_topic = self.app_config["producer_topic_complex"]

        self.log.info(data["message"], pid=pid)
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
