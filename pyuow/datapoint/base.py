import typing as t
from abc import ABC, abstractmethod
from dataclasses import dataclass

from .exceptions import DataPointIsNotProducedError

VALUE = t.TypeVar("VALUE", bound=t.Any)
NAME = t.TypeVar("NAME", bound="BaseDataPointName[t.Any]")


@dataclass(frozen=True)
class BaseDataPointName(t.Generic[VALUE]):
    raw: str

    def __call__(
        self, value: VALUE
    ) -> "BaseDataPoint[BaseDataPointName[VALUE], VALUE]":
        return BaseDataPoint(self, value)


@dataclass(frozen=True)
class BaseDataPoint(t.Generic[NAME, VALUE]):
    name: NAME
    value: VALUE


class DataPointDict(t.Dict[BaseDataPointName[VALUE], VALUE]):
    pass


class BaseDataPointProducer(ABC):
    @abstractmethod
    def add(
        self, *datapoints: BaseDataPoint[BaseDataPointName[t.Any], t.Any]
    ) -> None:
        raise NotImplementedError


class BaseDataPointConsumer(ABC):
    @abstractmethod
    def get(self, *names: BaseDataPointName[t.Any]) -> DataPointDict[t.Any]:
        raise NotImplementedError


class ConsumesDataPoints(ABC):
    @property
    @abstractmethod
    def _consumes(
        self, *names: BaseDataPointName[t.Any]
    ) -> t.Set[BaseDataPointName[t.Any]]:
        raise NotImplementedError

    def out_of(self, consumer: BaseDataPointConsumer) -> DataPointDict[t.Any]:
        return consumer.get(*self._consumes)


class ProducesDataPoints(ABC):
    @dataclass(frozen=True)
    class ProducerProxy:
        _producer: BaseDataPointProducer
        _required_names: t.Set[BaseDataPointName[t.Any]]

        def add(
            self, *datapoints: BaseDataPoint[BaseDataPointName[t.Any], t.Any]
        ) -> None:
            actual_names = {datapoint.name for datapoint in datapoints}
            missing = self._required_names - actual_names

            if len(missing) > 0:
                raise DataPointIsNotProducedError(missing)

            self._producer.add(*datapoints)

    @property
    @abstractmethod
    def _produces(
        self, *names: BaseDataPointName[t.Any]
    ) -> t.Set[BaseDataPointName[t.Any]]:
        raise NotImplementedError

    def to(self, producer: BaseDataPointProducer) -> ProducerProxy:
        return self.ProducerProxy(producer, self._produces)
