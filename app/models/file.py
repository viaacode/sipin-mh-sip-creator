from dataclasses import dataclass, field

from rdflib.term import Node


@dataclass(order=True)
class File:
    """Class representing a file of a representation."""

    sort_field: int = field(init=False, repr=False)
    sort_field2: str = field(init=False, repr=False)
    id: str
    filename: str
    fixity: str
    node: Node
    order: int

    def __post_init__(self):
        self.sort_field = self.order
        self.sort_field2 = self.filename
