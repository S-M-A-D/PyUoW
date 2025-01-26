import typing as t
from abc import ABC, abstractmethod
from copy import deepcopy
from dataclasses import dataclass, field, replace
from enum import Enum, auto, unique
from uuid import uuid4

from ..clock import offset_naive_utcnow
from ..entity import (
    AuditedEntity,
    Entity,
    SoftDeletableEntity,
    VersionedEntity,
)
from ..types import MISSING
from .event import ModelCreatedEvent, ModelDeletedEvent, ModelEvent

ENTITY_ID = t.TypeVar("ENTITY_ID", bound=t.Any)
ENTITY_TYPE = t.TypeVar("ENTITY_TYPE", bound=Entity[t.Any])
SELF = t.TypeVar("SELF", bound="Model[t.Any]")


@dataclass(frozen=True)
class Model(
    AuditedEntity[ENTITY_ID],
    SoftDeletableEntity[ENTITY_ID],
    VersionedEntity[ENTITY_ID],
    ABC,
):
    id: ENTITY_ID = t.cast(ENTITY_ID, MISSING)

    _events: t.Sequence[ModelEvent[ENTITY_ID]] = field(
        default_factory=t.Sequence, repr=False, compare=False
    )
    _is_new: bool = field(default=False, repr=False, compare=False)

    @abstractmethod
    def generate_id(self) -> ENTITY_ID:
        raise NotImplementedError

    def __post_init__(self) -> None:
        super().__post_init__()

        if self.id is MISSING:
            object.__setattr__(self, "id", self.generate_id())
            object.__setattr__(self, "_is_new", True)

    def update(
        self: SELF,
        event: t.Optional[ModelEvent[ENTITY_ID]] = None,
        **kwargs: t.Any,
    ) -> SELF:
        return replace(
            self,
            _events=[*self._events, event] if event else self._events,
            **kwargs,
        )

    def create(self: SELF) -> SELF:
        return self.update(
            ModelCreatedEvent(
                id=uuid4(),
                model_id=self.id,
                created_date=self.created_date,
            )
        )

    def delete(self: SELF) -> SELF:
        now = offset_naive_utcnow()
        return self.update(
            ModelDeletedEvent(id=uuid4(), model_id=self.id, deleted_date=now),
            deleted_date=now,
        )

    @property
    def is_new(self) -> bool:
        return self._is_new

    def events(self) -> t.Sequence[ModelEvent[ENTITY_ID]]:
        return deepcopy(self._events)


@unique
class ChangeType(Enum):
    ADD = auto()
    UPDATE = auto()
    DELETE = auto()


@dataclass(frozen=True)
class Change:
    type: ChangeType
    entity: Entity[t.Any]


@dataclass(frozen=True)
class Batch:
    is_shut: bool = field(default=False, init=False)

    _changes: t.Dict[t.Any, Change] = field(
        default_factory=dict, init=False, repr=False
    )

    def events(self) -> t.Sequence[ModelEvent[t.Any]]:
        return [
            event
            for change in self._changes.values()
            for event in t.cast(Model[t.Any], change.entity).events()
            if isinstance(change.entity, Model)
        ]

    def changes(self) -> t.Dict[ENTITY_ID, Change]:
        return deepcopy(self._changes)

    def add(self, entity: ENTITY_TYPE) -> ENTITY_TYPE:
        if isinstance(entity, Model) and not entity.is_new:
            raise RuntimeError("Can't add an existing entity")

        self._add_change(ChangeType.ADD, entity)
        return entity

    def update(self, entity: ENTITY_TYPE) -> ENTITY_TYPE:
        if isinstance(entity, Model) and entity.is_new:
            raise RuntimeError("Can't update a new entity")

        self._add_change(ChangeType.UPDATE, entity)
        return entity

    def delete(self, entity: ENTITY_TYPE) -> ENTITY_TYPE:
        if isinstance(entity, Model) and entity.is_new:
            raise RuntimeError("Can't delete a new entity")

        self._add_change(ChangeType.DELETE, entity)
        return entity

    def shut(self) -> None:
        object.__setattr__(self, "shut", True)

    def _add_change(
        self, change_type: ChangeType, entity: ENTITY_TYPE
    ) -> None:
        if self.is_shut:
            raise RuntimeError("Batch can't be changed, it's already shut")

        if existing := self._changes.get(entity.id):
            raise RuntimeError(
                f"{entity.id} has already been added to batch for {existing.type.value} operation"
            )

        self._changes[entity.id] = Change(type=change_type, entity=entity)
