import datetime
import typing as t
from dataclasses import dataclass
from uuid import UUID

from ...entity import Entity

ENTITY_ID = t.TypeVar("ENTITY_ID", bound=t.Any)
ENTITY_TYPE = t.TypeVar("ENTITY_TYPE", bound=Entity[t.Any])


@dataclass(frozen=True)
class ModelEvent(t.Generic[ENTITY_ID]):
    id: UUID
    model_id: ENTITY_ID


@dataclass(frozen=True)
class ModelCreatedEvent(ModelEvent[ENTITY_ID]):
    created_date: datetime.datetime


@dataclass(frozen=True)
class ModelDeletedEvent(ModelEvent[ENTITY_ID]):
    deleted_date: datetime.datetime
