from dataclasses import dataclass, field

from rdflib.term import Node

from app.models.file import File


@dataclass
class Representation:
    """Class representing a representation of an IE."""

    id: str
    label: str
    node: Node
    events: list[Node] = field(default_factory=list[Node])
    files: list[File] = field(default_factory=list[File])
