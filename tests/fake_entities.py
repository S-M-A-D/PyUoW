from __future__ import annotations

import datetime
import typing as t
from dataclasses import dataclass, replace
from uuid import UUID, uuid4

from pyuow.domain import Model
from pyuow.domain.event import ModelCreatedEvent, ModelDeletedEvent, ModelEvent
from pyuow.entity import (
    AuditedEntity,
    Entity,
    SoftDeletableEntity,
    VersionedEntity,
)

FakeEntityId = t.NewType("FakeEntityId", UUID)


@dataclass(frozen=True)
class FakeVersionedEntity(VersionedEntity[FakeEntityId]):
    field: str = "test"

    def change_field(self, value: str) -> FakeVersionedEntity:
        return replace(self, field=value)


@dataclass(frozen=True)
class FakeAuditedEntity(
    AuditedEntity[FakeEntityId], SoftDeletableEntity[FakeEntityId]
):
    field: str = "test"

    def change_field(self, value: str) -> FakeAuditedEntity:
        return replace(self, field=value)


@dataclass(frozen=True)
class FakeEntity(Entity[FakeEntityId]):
    field: str = "test"

    def change_field(self, value: str) -> FakeEntity:
        return replace(self, field=value)


FakeModelId = t.NewType("FakeModelId", UUID)


@dataclass(frozen=True)
class FakeModelCreatedEvent(ModelCreatedEvent[FakeModelId]):
    field: str


@dataclass(frozen=True)
class FakeModelUpdatedEvent(ModelEvent[FakeModelId]):
    new_field: str


@dataclass(frozen=True)
class FakeModelDeletedEvent(ModelDeletedEvent[FakeModelId]):
    pass


@dataclass(frozen=True)
class FakeModel(Model[FakeModelId]):
    field: str = "test"

    def _generate_id(self) -> FakeModelId:
        return FakeModelId(uuid4())

    def _created_event(self, date: datetime.datetime) -> FakeModelCreatedEvent:
        return FakeModelCreatedEvent(
            id=uuid4(), model_id=self.id, field=self.field, created_date=date
        )

    def _deleted_event(self, date: datetime.datetime) -> FakeModelDeletedEvent:
        return FakeModelDeletedEvent(
            id=uuid4(), model_id=self.id, deleted_date=date
        )

    def change_field(self, value: str) -> FakeModel:
        return self.update(
            event=FakeModelUpdatedEvent(
                id=uuid4(),
                model_id=self.id,
                new_field=value,
            ),
            field=value,
        )
