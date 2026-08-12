import abc
import typing as t
from abc import ABC

from ...entity import Entity

ENTITY_ID = t.TypeVar("ENTITY_ID", bound=t.Hashable)
ENTITY_TYPE = t.TypeVar("ENTITY_TYPE", bound=Entity[t.Any])
VIEW_TYPE = t.TypeVar("VIEW_TYPE")
CRITERIA = t.TypeVar("CRITERIA")


class BaseReadOnlyEntityRepository(t.Generic[ENTITY_ID, ENTITY_TYPE], ABC):
    @abc.abstractmethod
    async def find(self, entity_id: ENTITY_ID) -> t.Optional[ENTITY_TYPE]:
        raise NotImplementedError

    @abc.abstractmethod
    async def find_all(
        self, entity_ids: t.Iterable[ENTITY_ID]
    ) -> t.Iterable[ENTITY_TYPE]:
        raise NotImplementedError

    @abc.abstractmethod
    async def get(self, entity_id: ENTITY_ID) -> ENTITY_TYPE:
        raise NotImplementedError

    @abc.abstractmethod
    async def exists(self, entity_id: ENTITY_ID) -> bool:
        raise NotImplementedError


class BaseWriteOnlyEntityRepository(t.Generic[ENTITY_ID, ENTITY_TYPE], ABC):
    @abc.abstractmethod
    async def add(self, entity: ENTITY_TYPE) -> ENTITY_TYPE:
        raise NotImplementedError

    @abc.abstractmethod
    async def add_all(
        self, entities: t.Sequence[ENTITY_TYPE]
    ) -> t.Iterable[ENTITY_TYPE]:
        raise NotImplementedError

    @abc.abstractmethod
    async def update(self, entity: ENTITY_TYPE) -> ENTITY_TYPE:
        raise NotImplementedError

    @abc.abstractmethod
    async def update_all(
        self, entities: t.Sequence[ENTITY_TYPE]
    ) -> t.Iterable[ENTITY_TYPE]:
        raise NotImplementedError

    @abc.abstractmethod
    async def delete(self, entity: ENTITY_TYPE) -> bool:
        raise NotImplementedError

    @abc.abstractmethod
    async def delete_all(self, entities: t.Sequence[ENTITY_TYPE]) -> bool:
        raise NotImplementedError


class BaseEntityRepository(
    BaseReadOnlyEntityRepository[ENTITY_ID, ENTITY_TYPE],
    BaseWriteOnlyEntityRepository[ENTITY_ID, ENTITY_TYPE],
    ABC,
):
    pass


class BaseViewRepository(t.Generic[VIEW_TYPE, CRITERIA], ABC):
    @abc.abstractmethod
    async def find_by(self, criteria: CRITERIA) -> t.Optional[VIEW_TYPE]:
        raise NotImplementedError

    @abc.abstractmethod
    async def find_all_by(self, criteria: CRITERIA) -> t.Iterable[VIEW_TYPE]:
        raise NotImplementedError

    @abc.abstractmethod
    async def get_by(self, criteria: CRITERIA) -> VIEW_TYPE:
        raise NotImplementedError

    @abc.abstractmethod
    async def exists_by(self, criteria: CRITERIA) -> bool:
        raise NotImplementedError


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


class BaseViewRepositoryFactory(ABC):
    @property
    @abc.abstractmethod
    def views(
        self,
    ) -> t.Mapping[
        t.Type[t.Any],
        BaseViewRepository[t.Any, t.Any],
    ]:
        raise NotImplementedError

    def view_for(
        self, view_type: t.Type[VIEW_TYPE]
    ) -> BaseViewRepository[VIEW_TYPE, t.Any]:
        try:
            return self.views[view_type]
        except KeyError as e:
            raise KeyError(
                f"View repository for {view_type.__name__} is not registered"
            ) from e
