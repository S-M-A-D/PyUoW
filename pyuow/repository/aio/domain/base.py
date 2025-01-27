import typing as t
from abc import ABC
from itertools import groupby

from ....domain import Batch, ChangeType, Model
from ....domain.event import ModelEvent
from ....repository.aio import BaseRepositoryFactory
from ....repository.aio.base import ENTITY_TYPE


class BaseDomainRepository(ABC):
    def __init__(
        self,
        *,
        repositories: BaseRepositoryFactory,
        events_handler: t.Callable[
            [t.Sequence[ModelEvent[t.Any]]], t.Awaitable[None]
        ],
    ) -> None:
        self._repositories = repositories
        self._events_handler = events_handler

    async def process_batch(self, batch: Batch) -> None:
        batch.shut()

        for (change_type, _), changes in groupby(
            batch.changes().values(), lambda c: (c.type, type(c.entity))
        ):
            entities = [change.entity for change in changes]

            if change_type == ChangeType.ADD:
                await self._add_all(entities)
            if change_type == ChangeType.UPDATE:
                await self._update_all(entities)
            if change_type == ChangeType.DELETE:
                await self._delete_all(entities)

        await self._events_handler(batch.events())

    async def _add(self, entity: ENTITY_TYPE) -> ENTITY_TYPE:
        return t.cast(
            ENTITY_TYPE,
            await self._repositories.repo_for(type(entity)).add(entity),
        )

    async def _add_all(
        self, entities: t.Sequence[ENTITY_TYPE]
    ) -> t.Iterable[ENTITY_TYPE]:
        return [await self._add(entity) for entity in entities]

    async def _update(self, entity: ENTITY_TYPE) -> ENTITY_TYPE:
        return t.cast(
            ENTITY_TYPE,
            await self._repositories.repo_for(type(entity)).update(entity),
        )

    async def _update_all(
        self, entities: t.Sequence[ENTITY_TYPE]
    ) -> t.Iterable[ENTITY_TYPE]:
        return [await self._update(entity) for entity in entities]

    async def _delete(self, entity: ENTITY_TYPE) -> bool:
        deleted_entity = (
            (entity if entity.is_deleted else entity.delete())
            if isinstance(entity, Model)
            else entity
        )
        return await self._repositories.repo_for(type(deleted_entity)).delete(
            deleted_entity
        )

    async def _delete_all(self, entities: t.Sequence[ENTITY_TYPE]) -> bool:
        return all([await self._delete(entity) for entity in entities])
