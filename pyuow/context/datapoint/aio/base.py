from abc import ABC
from dataclasses import dataclass

from ....context import BaseContext
from ....datapoint.aio import BaseDataPointConsumer, BaseDataPointProducer
from ..base import PARAMS


@dataclass(frozen=True)
class BaseDataPointProducerContext(
    BaseContext[PARAMS], BaseDataPointProducer, ABC
):
    pass


@dataclass(frozen=True)
class BaseDataPointConsumerContext(
    BaseContext[PARAMS], BaseDataPointConsumer, ABC
):
    pass


@dataclass(frozen=True)
class BaseDataPointContext(
    BaseDataPointProducerContext[PARAMS],
    BaseDataPointConsumerContext[PARAMS],
    ABC,
):
    pass
