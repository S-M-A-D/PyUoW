import abc
import typing as t
from abc import ABC
from itertools import groupby

from ..domain import Batch, ChangeType, Model
from ..domain.event import ModelEvent
from ..entity import Entity

ENTITY_ID = t.TypeVar("ENTITY_ID", bound=t.Any)
ENTITY_TYPE = t.TypeVar("ENTITY_TYPE", bound=Entity[t.Any])


class BaseReadOnlyEntityRepository(t.Generic[ENTITY_ID, ENTITY_TYPE], ABC):
    @abc.abstractmethod
    def find(self, entity_id: ENTITY_ID) -> t.Optional[ENTITY_TYPE]:
        raise NotImplementedError

    @abc.abstractmethod
    def find_all(
        self, entity_ids: t.Iterable[ENTITY_ID]
    ) -> t.Iterable[ENTITY_TYPE]:
        raise NotImplementedError

    @abc.abstractmethod
    def get(self, entity_id: ENTITY_ID) -> ENTITY_TYPE:
        raise NotImplementedError

    @abc.abstractmethod
    def exists(self, entity_id: ENTITY_ID) -> bool:
        raise NotImplementedError


class BaseWriteOnlyEntityRepository(t.Generic[ENTITY_ID, ENTITY_TYPE], ABC):
    @abc.abstractmethod
    def add(self, entity: ENTITY_TYPE) -> ENTITY_TYPE:
        raise NotImplementedError

    @abc.abstractmethod
    def add_all(
        self, entities: t.Sequence[ENTITY_TYPE]
    ) -> t.Iterable[ENTITY_TYPE]:
        raise NotImplementedError

    @abc.abstractmethod
    def update(self, entity: ENTITY_TYPE) -> ENTITY_TYPE:
        raise NotImplementedError

    @abc.abstractmethod
    def update_all(
        self, entities: t.Sequence[ENTITY_TYPE]
    ) -> t.Iterable[ENTITY_TYPE]:
        raise NotImplementedError

    @abc.abstractmethod
    def delete(self, entity: ENTITY_TYPE) -> bool:
        raise NotImplementedError

    @abc.abstractmethod
    def delete_all(self, entities: t.Sequence[ENTITY_TYPE]) -> bool:
        raise NotImplementedError


class BaseEntityRepository(
    BaseReadOnlyEntityRepository[ENTITY_ID, ENTITY_TYPE],
    BaseWriteOnlyEntityRepository[ENTITY_ID, ENTITY_TYPE],
    ABC,
):
    pass


class BaseRepositoryFactory(ABC):
    @property
    @abc.abstractmethod
    def repositories(
        self,
    ) -> t.Mapping[
        t.Type[Entity[t.Any]],
        BaseEntityRepository[t.Any, t.Any],
    ]:
        raise NotImplementedError

    def repo_for(
        self, entity_type: t.Type[ENTITY_TYPE]
    ) -> BaseEntityRepository[t.Any, t.Any]:
        try:
            return self.repositories[entity_type]
        except KeyError as e:
            raise KeyError(
                f"Repository for {entity_type.__name__} is not registered"
            ) from e


class BaseDomainRepository(ABC):
    def __init__(
        self,
        *,
        repositories: BaseRepositoryFactory,
        events_handler: t.Callable[[t.Sequence[ModelEvent[t.Any]]], None],
    ) -> None:
        self._repositories = repositories
        self._events_handler = events_handler

    def process_batch(self, batch: Batch) -> None:
        batch.shut()

        for (change_type, _), changes in groupby(
            batch.changes().values(), lambda c: (c.type, type(c.entity))
        ):
            entities = [change.entity for change in changes]

            if change_type == ChangeType.ADD:
                self._add_all(entities)
            if change_type == ChangeType.UPDATE:
                self._update_all(entities)
            if change_type == ChangeType.DELETE:
                self._delete_all(entities)

        self._events_handler(batch.events())

    def _add(self, entity: ENTITY_TYPE) -> ENTITY_TYPE:
        new_entity = entity.create() if isinstance(entity, Model) else entity
        return t.cast(
            ENTITY_TYPE,
            self._repositories.repo_for(type(new_entity)).add(new_entity),
        )

    def _add_all(
        self, entities: t.Sequence[ENTITY_TYPE]
    ) -> t.Iterable[ENTITY_TYPE]:
        return [self._add(entity) for entity in entities]

    def _update(self, entity: ENTITY_TYPE) -> ENTITY_TYPE:
        return t.cast(
            ENTITY_TYPE,
            self._repositories.repo_for(type(entity)).update(entity),
        )

    def _update_all(
        self, entities: t.Sequence[ENTITY_TYPE]
    ) -> t.Iterable[ENTITY_TYPE]:
        return [self._update(entity) for entity in entities]

    def _delete(self, entity: ENTITY_TYPE) -> bool:
        deleted_entity = (
            entity.delete() if isinstance(entity, Model) else entity
        )
        return self._repositories.repo_for(type(deleted_entity)).delete(
            deleted_entity
        )

    def _delete_all(self, entities: t.Sequence[ENTITY_TYPE]) -> bool:
        return all([self._delete(entity) for entity in entities])
