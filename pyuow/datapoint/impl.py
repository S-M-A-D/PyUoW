import typing as t
from abc import ABC, abstractmethod
from dataclasses import dataclass

from ..datapoint import (
    BaseDataPoint,
    BaseDataPointConsumer,
    BaseDataPointContainer,
    BaseDataPointProducer,
    DataPointDict,
    DataPointIsNotProducedError,
)


class ConsumesDataPoints(ABC):
    @property
    @abstractmethod
    def _consumes(
        self, *specs: BaseDataPoint[t.Any]
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
        self, *specs: BaseDataPoint[t.Any]
    ) -> t.Set[BaseDataPoint[t.Any]]:
        raise NotImplementedError

    def to(self, producer: BaseDataPointProducer) -> ProducerProxy:
        return self.ProducerProxy(producer, self._produces)
