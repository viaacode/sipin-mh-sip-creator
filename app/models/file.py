from dataclasses import dataclass


@dataclass
class File:
    """Class representing a file of a representation."""

    id: str
    filename: str
    fixity: str
