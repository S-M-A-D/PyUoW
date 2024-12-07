import typing as t
from abc import ABC, abstractmethod
from dataclasses import dataclass

VALUE = t.TypeVar("VALUE", bound=t.Any)


@dataclass(frozen=True)
class BaseDataPoint(t.Generic[VALUE]):
    name: str
    ref_type: t.Type[VALUE]

    def __call__(self, value: VALUE) -> "BaseDataPointContainer[VALUE]":
        return BaseDataPointContainer(self, value)


@dataclass(frozen=True)
class BaseDataPointContainer(t.Generic[VALUE]):
    spec: BaseDataPoint[VALUE]
    value: VALUE


class DataPointDict(t.Dict[BaseDataPoint[VALUE], VALUE]):
    pass


class BaseDataPointProducer(ABC):
    @abstractmethod
    def add(self, *datapoints: BaseDataPointContainer[t.Any]) -> None:
        raise NotImplementedError


class BaseDataPointConsumer(ABC):
    @abstractmethod
    def get(self, *specs: BaseDataPoint[t.Any]) -> DataPointDict[t.Any]:
        raise NotImplementedError
