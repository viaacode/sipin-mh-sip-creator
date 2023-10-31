from dataclasses import dataclass, field

from app.models.intellectual_entity import IntellectualEntity
from app.models.representation import Representation


@dataclass
class SIP:
    """Class representing a SIP."""

    id: str
    profile: str
    batch_id: str = ""
    intellectual_entities: list[IntellectualEntity] = field(
        default_factory=list[IntellectualEntity]
    )
    representations: list[Representation] = field(default_factory=list[Representation])
