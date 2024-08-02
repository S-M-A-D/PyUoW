import typing as t
from abc import ABC
from dataclasses import dataclass

from ...context import BaseContext
from ...datapoint import BaseDataPointConsumer, BaseDataPointProducer
from ..base import BaseParams

PARAMS = t.TypeVar("PARAMS", bound=BaseParams)


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
