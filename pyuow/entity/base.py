import typing as t
from dataclasses import dataclass
from datetime import datetime

from ..clock import offset_naive_utcnow
from ..types import MISSING

ENTITY_ID = t.TypeVar("ENTITY_ID", bound=t.Any)
ENTITY_TYPE = t.TypeVar("ENTITY_TYPE", bound="Entity[t.Any]")


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
