from dataclasses import dataclass, field
from rdflib.term import Node
from app.models.representation import Representation


@dataclass
class IntellectualEntity:
    """Class representing an intellectual entity."""

    id: str
    label: str
    node: Node
    representations: list[Representation] = field(default_factory=list[Representation])
