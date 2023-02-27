from dataclasses import dataclass, field

from app.models.file import File


@dataclass
class Representation:
    """Class representing a representation of an IE."""

    id: str
    files: list[File] = field(default_factory=list[File])
