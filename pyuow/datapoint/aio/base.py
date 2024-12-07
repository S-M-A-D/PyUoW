import typing as t
from abc import ABC, abstractmethod

from ..base import BaseDataPointContainer, BaseDataPointSpec, DataPointDict


class BaseDataPointProducer(ABC):
    @abstractmethod
    async def add(self, *datapoints: BaseDataPointContainer[t.Any]) -> None:
        raise NotImplementedError


class BaseDataPointConsumer(ABC):
    @abstractmethod
    async def get(
        self, *specs: BaseDataPointSpec[t.Any]
    ) -> DataPointDict[t.Any]:
        raise NotImplementedError
