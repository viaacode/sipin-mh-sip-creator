import requests
from viaa.configuration import ConfigParser
from viaa.observability import logging


class PidClient:
    """Abstraction for a PID webservice.

    Attributes:
        log: The logger.
        pid_config: The config regarding the PID webservice.
    """

    def __init__(self):
        config_parser = ConfigParser()
        self.log = logging.get_logger(__name__, config=config_parser)
        self.pid_config: dict = config_parser.app_cfg["pid"]

    def get_pid(self) -> str:
        """Retrieve a new PID from the PID webservice."""

        resp = requests.get(self.pid_config["url"])
        pid = resp.json()[0]["id"]

        return pid
