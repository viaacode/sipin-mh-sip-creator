import shutil
from pathlib import Path
import json

import rdflib
from cloudevents.events import (
    CEMessageMode,
    Event,
    EventAttributes,
    EventOutcome,
    PulsarBinding,
)

# from helpers.xml import build_mh_sidecar
from app.services.pid import PidClient
from app.services.pulsar import PulsarClient
from viaa.configuration import ConfigParser
from viaa.observability import logging

from app.helpers import graph, xml

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
        self.producer_topic = self.app_config["producer_topic"]

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
        metadata_graph = graph.parse_graph(json.dumps(event.get_data()["metadata_graph"]))

        # Path to unzipped bag
        # `/opt/sipin/unzip/<name>.bag.zip`
        path: str = event.get_attributes()["subject"]
        pid = self.pid_client.get_pid()
        representations = graph.get_representations(metadata_graph)

        if len(representations) == 1 and len(representations[0].files) == 1:
            # We make essence + sidecar ready for tra
            sidecar = xml.build_mh_sidecar(metadata_graph)
            cp_id = graph.get_cp_id_from_graph(metadata_graph)
            filename = Path(representations[0].files[0].filename)

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
                "pid": pid,
                "outcome": EventOutcome.SUCCESS,
                "message": f"AIP created: sidecar ingest for {filename}",
            }

            self.log.info(data["message"])
        else:
            # A MH 2.0 complex should be created coming in v0.2
            pass
        self.produce_event(self.producer_topic, data, path, EventOutcome.SUCCESS, event.correlation_id)

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
