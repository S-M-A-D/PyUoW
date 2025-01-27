import typing as t
from dataclasses import dataclass
from datetime import datetime

from ..clock import offset_naive_utcnow
from ..types import MISSING

ENTITY_ID = t.TypeVar("ENTITY_ID", bound=t.Any)
ENTITY_TYPE = t.TypeVar("ENTITY_TYPE", bound="Entity[t.Any]")
SELF = t.TypeVar("SELF", bound="Entity[t.Any]")


class Version(int):
    def __new__(cls, value: int) -> "Version":
        if value < 0:
            raise ValueError("Version cannot be negative")

        return super().__new__(cls, value)

    def next(self) -> "Version":
        return Version(self + 1)


@dataclass(frozen=True)
class Entity(t.Generic[ENTITY_ID]):
    id: ENTITY_ID


@dataclass(frozen=True)
class AuditedEntity(Entity[ENTITY_ID]):
    created_date: datetime = t.cast(datetime, MISSING)
    updated_date: datetime = t.cast(datetime, MISSING)

    def __post_init__(self) -> None:
        now = offset_naive_utcnow()

        if self.created_date is MISSING:
            object.__setattr__(self, "created_date", now)
        if self.updated_date is MISSING:
            object.__setattr__(self, "updated_date", now)


@dataclass(frozen=True)
class SoftDeletableEntity(Entity[ENTITY_ID]):
    deleted_date: t.Optional[datetime] = None


@dataclass(frozen=True)
class VersionedEntity(Entity[ENTITY_ID]):
    version: Version = Version(0)
