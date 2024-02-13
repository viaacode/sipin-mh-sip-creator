from dataclasses import dataclass, field

from rdflib.term import Node

from app.models.file import File


@dataclass(order=True)
class Representation:
    """Class representing a representation of an IE."""

    sort_field: str = field(init=False, repr=False)
    id: str
    label: str
    node: Node
    events: list[Node] = field(default_factory=list[Node])
    files: list[File] = field(default_factory=list[File])
    
    def __post_init__(self):
        self.sort_field = self.label