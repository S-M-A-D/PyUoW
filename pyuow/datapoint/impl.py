import typing as t
from abc import ABC, abstractmethod
from dataclasses import dataclass

from ..datapoint import (
    BaseDataPointConsumer,
    BaseDataPointContainer,
    BaseDataPointProducer,
    BaseDataPointSpec,
    DataPointIsNotProducedError,
)


class ConsumesDataPoints(ABC):
    @property
    @abstractmethod
    def _consumes(
        self, *specs: BaseDataPointSpec[t.Any]
    ) -> t.Set[BaseDataPointSpec[t.Any]]:
        raise NotImplementedError

    def out_of(
        self, consumer: BaseDataPointConsumer[t.Any]
    ) -> t.Dict[BaseDataPointSpec[t.Any], t.Any]:
        consumed = consumer.get(*self._consumes)
        consumed_specs = set(consumed.keys())

        if not self._consumes.issubset(consumed_specs):
            raise DataPointIsNotProducedError(consumed_specs)

        return consumed


class ProducesDataPoints(ABC):
    @dataclass(frozen=True)
    class ProducerProxy:
        _producer: BaseDataPointProducer[t.Any]
        _required_names: t.Set[BaseDataPointSpec[t.Any]]

        def add(self, *datapoints: BaseDataPointContainer[t.Any]) -> None:
            actual_specs = {datapoint.spec for datapoint in datapoints}
            missing = self._required_names - actual_specs

            if len(missing) > 0:
                raise DataPointIsNotProducedError(missing)

            self._producer.add(*datapoints)

    @property
    @abstractmethod
    def _produces(
        self, *specs: BaseDataPointSpec[t.Any]
    ) -> t.Set[BaseDataPointSpec[t.Any]]:
        raise NotImplementedError

    def to(self, producer: BaseDataPointProducer[t.Any]) -> ProducerProxy:
        return self.ProducerProxy(producer, self._produces)
