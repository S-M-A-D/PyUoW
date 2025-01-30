import datetime
import typing as t
from dataclasses import dataclass, field
from uuid import UUID

from ...clock import nano_timestamp_utc
from ...entity import Entity

ENTITY_ID = t.TypeVar("ENTITY_ID", bound=t.Any)
ENTITY_TYPE = t.TypeVar("ENTITY_TYPE", bound=Entity[t.Any])


@dataclass(frozen=True)
class ModelEvent(t.Generic[ENTITY_ID]):
    id: UUID
    model_id: ENTITY_ID
    occurred_at: int = field(
        default_factory=nano_timestamp_utc,
        init=False,
        repr=False,
        compare=False,
    )


@dataclass(frozen=True)
class ModelCreatedEvent(ModelEvent[ENTITY_ID]):
    created_date: datetime.datetime


@dataclass(frozen=True)
class ModelDeletedEvent(ModelEvent[ENTITY_ID]):
    deleted_date: datetime.datetime
