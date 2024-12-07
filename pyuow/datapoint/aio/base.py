import typing as t
from abc import ABC, abstractmethod
from dataclasses import dataclass

from ..base import BaseDataPoint, BaseDataPointContainer, DataPointDict
from ..exceptions import DataPointIsNotProducedError


class BaseDataPointProducer(ABC):
    @abstractmethod
    async def add(self, *datapoints: BaseDataPointContainer[t.Any]) -> None:
        raise NotImplementedError


class BaseDataPointConsumer(ABC):
    @abstractmethod
    async def get(self, *names: BaseDataPoint[t.Any]) -> DataPointDict[t.Any]:
        raise NotImplementedError


class ConsumesDataPoints(ABC):
    @property
    @abstractmethod
    def _consumes(
        self, *names: BaseDataPoint[t.Any]
    ) -> t.Set[BaseDataPoint[t.Any]]:
        raise NotImplementedError

    async def out_of(
        self, consumer: BaseDataPointConsumer
    ) -> DataPointDict[t.Any]:
        return await consumer.get(*self._consumes)


class ProducesDataPoints(ABC):
    @dataclass(frozen=True)
    class ProducerProxy:
        _producer: BaseDataPointProducer
        _required_names: t.Set[BaseDataPoint[t.Any]]

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
        self, *names: BaseDataPoint[t.Any]
    ) -> t.Set[BaseDataPoint[t.Any]]:
        raise NotImplementedError

    def to(self, producer: BaseDataPointProducer) -> ProducerProxy:
        return self.ProducerProxy(producer, self._produces)
