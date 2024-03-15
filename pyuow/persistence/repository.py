import abc
import typing as t
from abc import ABC

from .entity import ENTITY_ID, ENTITY_TYPE, Entity


class BaseEntityRepository(t.Generic[ENTITY_ID, ENTITY_TYPE], ABC):
    @abc.abstractmethod
    def get(self, entity_id: ENTITY_ID) -> ENTITY_TYPE:
        ...

    @abc.abstractmethod
    def add(self, entity: ENTITY_TYPE) -> ENTITY_TYPE:
        ...

    @abc.abstractmethod
    def update(self, entity: ENTITY_TYPE) -> ENTITY_TYPE:
        ...

    @abc.abstractmethod
    def delete(self, entity: ENTITY_TYPE) -> bool:
        ...


class BaseRepositoryFactory(ABC):
    @property
    @abc.abstractmethod
    def repositories(
        self,
    ) -> t.Mapping[t.Type[Entity[t.Any]], BaseEntityRepository[t.Any, t.Any]]:
        ...

    def repo_for(
        self, entity_type: t.Type[ENTITY_TYPE]
    ) -> BaseEntityRepository[t.Any, t.Any]:
        try:
            return self.repositories[entity_type]
        except KeyError as e:
            raise ValueError(
                f"Repository for {entity_type.__name__} is not registered."
            ) from e
