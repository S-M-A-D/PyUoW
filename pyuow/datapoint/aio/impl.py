import typing as t
from abc import ABC, abstractmethod
from dataclasses import dataclass

from ...datapoint import (
    BaseDataPointContainer,
    BaseDataPointSpec,
    DataPointDict,
    DataPointIsNotProducedError,
)
from ...datapoint.aio import BaseDataPointConsumer, BaseDataPointProducer


class ConsumesDataPoints(ABC):
    @property
    @abstractmethod
    def _consumes(
        self, *specs: BaseDataPointSpec[t.Any]
    ) -> t.Set[BaseDataPointSpec[t.Any]]:
        raise NotImplementedError

    async def out_of(
        self, consumer: BaseDataPointConsumer
    ) -> DataPointDict[t.Any]:
        return await consumer.get(*self._consumes)


class ProducesDataPoints(ABC):
    @dataclass(frozen=True)
    class ProducerProxy:
        _producer: BaseDataPointProducer
        _required_names: t.Set[BaseDataPointSpec[t.Any]]

        async def add(
            self, *datapoints: BaseDataPointContainer[t.Any]
        ) -> None:
            actual_names = {datapoint.spec for datapoint in datapoints}
            missing = self._required_names - actual_names

            if len(missing) > 0:
                raise DataPointIsNotProducedError(missing)

            await self._producer.add(*datapoints)

    @property
    @abstractmethod
    def _produces(
        self, *specs: BaseDataPointSpec[t.Any]
    ) -> t.Set[BaseDataPointSpec[t.Any]]:
        raise NotImplementedError

    def to(self, producer: BaseDataPointProducer) -> ProducerProxy:
        return self.ProducerProxy(producer, self._produces)
