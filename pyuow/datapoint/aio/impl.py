import typing as t
from abc import ABC, abstractmethod
from dataclasses import dataclass

from ...datapoint import (
    BaseDataPointContainer,
    BaseDataPointsDict,
    BaseDataPointSpec,
    DataPointIsNotProducedError,
)
from ...datapoint.aio import BaseDataPointConsumer, BaseDataPointProducer


class ConsumesDataPoints(ABC):
    @property
    @abstractmethod
    def _consumes(self) -> t.Set[BaseDataPointSpec[t.Any]]:
        raise NotImplementedError

    async def out_of(
        self, consumer: BaseDataPointConsumer[t.Any]
    ) -> BaseDataPointsDict:
        consumed = await consumer.get(*self._consumes)
        consumed_specs = set(consumed.keys())

        if not self._consumes.issubset(consumed_specs):
            missing_specs = self._consumes - consumed_specs
            raise DataPointIsNotProducedError(missing_specs)

        return t.cast(BaseDataPointsDict, consumed)


class ProducesDataPoints(ABC):
    @dataclass(frozen=True)
    class ProducerProxy:
        _producer: BaseDataPointProducer[t.Any]
        _required_specs: t.Set[BaseDataPointSpec[t.Any]]

        async def add(
            self, *datapoints: BaseDataPointContainer[t.Any]
        ) -> None:
            actual_specs = {datapoint.spec for datapoint in datapoints}
            missing_specs = self._required_specs - actual_specs

            if len(missing_specs) > 0:
                raise DataPointIsNotProducedError(missing_specs)

            await self._producer.add(*datapoints)

    @property
    @abstractmethod
    def _produces(self) -> t.Set[BaseDataPointSpec[t.Any]]:
        raise NotImplementedError

    def to(self, producer: BaseDataPointProducer[t.Any]) -> ProducerProxy:
        return self.ProducerProxy(producer, self._produces)
