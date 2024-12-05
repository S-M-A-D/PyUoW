import typing as t
from abc import ABC, abstractmethod
from dataclasses import dataclass

from .exceptions import DataPointIsNotProducedError

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
    def get(self, *names: BaseDataPoint[t.Any]) -> DataPointDict[t.Any]:
        raise NotImplementedError


class ConsumesDataPoints(ABC):
    @property
    @abstractmethod
    def _consumes(
        self, *names: BaseDataPoint[t.Any]
    ) -> t.Set[BaseDataPoint[t.Any]]:
        raise NotImplementedError

    def out_of(self, consumer: BaseDataPointConsumer) -> DataPointDict[t.Any]:
        return consumer.get(*self._consumes)


class ProducesDataPoints(ABC):
    @dataclass(frozen=True)
    class ProducerProxy:
        _producer: BaseDataPointProducer
        _required_names: t.Set[BaseDataPoint[t.Any]]

        def add(self, *datapoints: BaseDataPointContainer[t.Any]) -> None:
            actual_names = {datapoint.spec for datapoint in datapoints}
            missing = self._required_names - actual_names

            if len(missing) > 0:
                raise DataPointIsNotProducedError(missing)

            self._producer.add(*datapoints)

    @property
    @abstractmethod
    def _produces(
        self, *names: BaseDataPoint[t.Any]
    ) -> t.Set[BaseDataPoint[t.Any]]:
        raise NotImplementedError

    def to(self, producer: BaseDataPointProducer) -> ProducerProxy:
        return self.ProducerProxy(producer, self._produces)
