from dataclasses import dataclass

from rdflib.term import Node


@dataclass
class File:
    """Class representing a file of a representation."""

    id: str
    filename: str
    fixity: str
    node: Node
