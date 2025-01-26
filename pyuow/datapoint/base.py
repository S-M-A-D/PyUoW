import typing as t
from abc import ABC, abstractmethod
from dataclasses import dataclass

VALUE = t.TypeVar("VALUE", bound=t.Any)


@dataclass(frozen=True)
class BaseDataPointSpec(t.Generic[VALUE]):
    name: str
    ref_type: t.Type[VALUE]

    def __call__(self, value: VALUE) -> "BaseDataPointContainer[VALUE]":
        return BaseDataPointContainer(self, value)


@dataclass(frozen=True)
class BaseDataPointContainer(t.Generic[VALUE]):
    spec: BaseDataPointSpec[VALUE]
    value: VALUE


class BaseDataPointsDict(dict[BaseDataPointSpec[t.Any], t.Any]):
    def __getitem__(self, key: BaseDataPointSpec[VALUE]) -> VALUE:
        return t.cast(VALUE, super().__getitem__(key))  # pragma: no cover


DATA_POINT_CONTAINER = t.TypeVar(
    "DATA_POINT_CONTAINER", bound=BaseDataPointContainer[t.Any]
)


class BaseDataPointProducer(t.Generic[DATA_POINT_CONTAINER], ABC):
    @abstractmethod
    def add(self, *datapoints: DATA_POINT_CONTAINER) -> None:
        raise NotImplementedError


DATA_POINT_SPEC = t.TypeVar("DATA_POINT_SPEC", bound=BaseDataPointSpec[t.Any])


class BaseDataPointConsumer(t.Generic[DATA_POINT_SPEC], ABC):
    @abstractmethod
    def get(self, *specs: DATA_POINT_SPEC) -> t.Dict[DATA_POINT_SPEC, t.Any]:
        raise NotImplementedError
