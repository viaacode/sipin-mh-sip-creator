from dataclasses import dataclass


@dataclass
class Organization:
    """Class representing an organization."""

    id: str
    label: str
