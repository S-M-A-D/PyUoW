import typing as t
from abc import ABC, abstractmethod
from dataclasses import dataclass

from pyuow import DataPointIsNotProducedError

from ..base import (
    AnyDatapoint,
    AnyDataPointName,
    BaseDataPointName,
    DataPointDict,
)


class BaseDataPointProducer(ABC):
    @abstractmethod
    async def add(self, *datapoints: AnyDatapoint) -> None:
        raise NotImplementedError


class BaseDataPointConsumer(ABC):
    @abstractmethod
    async def get(self, *names: AnyDataPointName) -> DataPointDict[t.Any]:
        raise NotImplementedError


class ConsumesDataPoints(ABC):
    @property
    @abstractmethod
    def _consumes(
        self, *names: AnyDataPointName
    ) -> t.Set[BaseDataPointName[t.Any]]:
        raise NotImplementedError

    async def out_of(
        self, consumer: BaseDataPointConsumer
    ) -> DataPointDict[t.Any]:
        return await consumer.get(*self._consumes)


class ProducesDataPoints(ABC):
    @dataclass(frozen=True)
    class ProducerProxy:
        _producer: BaseDataPointProducer
        _required_names: t.Set[AnyDataPointName]

        async def add(self, *datapoints: AnyDatapoint) -> None:
            actual_names = {datapoint.name for datapoint in datapoints}
            missing = self._required_names - actual_names

            if len(missing) > 0:
                raise DataPointIsNotProducedError(missing)

            await self._producer.add(*datapoints)

    @property
    @abstractmethod
    def _produces(
        self, *names: AnyDataPointName
    ) -> t.Set[BaseDataPointName[t.Any]]:
        raise NotImplementedError

    def to(self, producer: BaseDataPointProducer) -> ProducerProxy:
        return self.ProducerProxy(producer, self._produces)
