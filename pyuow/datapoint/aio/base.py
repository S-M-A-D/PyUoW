import typing as t
from abc import ABC, abstractmethod

from ..base import BaseDataPointContainer, BaseDataPointSpec

DATA_POINT_CONTAINER = t.TypeVar(
    "DATA_POINT_CONTAINER", bound=BaseDataPointContainer[t.Any]
)


class BaseDataPointProducer(t.Generic[DATA_POINT_CONTAINER], ABC):
    @abstractmethod
    async def add(self, *datapoints: DATA_POINT_CONTAINER) -> None:
        raise NotImplementedError


DATA_POINT_SPEC = t.TypeVar("DATA_POINT_SPEC", bound=BaseDataPointSpec[t.Any])


class BaseDataPointConsumer(t.Generic[DATA_POINT_SPEC], ABC):
    @abstractmethod
    async def get(
        self, *specs: DATA_POINT_SPEC
    ) -> t.Dict[DATA_POINT_SPEC, t.Any]:
        raise NotImplementedError
