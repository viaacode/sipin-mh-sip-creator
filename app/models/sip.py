from dataclasses import dataclass, field

from app.models.representation import Representation


@dataclass
class SIP:
    """Class representing a SIP."""

    id: str
    profile: str
    representations: list[Representation] = field(default_factory=list[Representation])
