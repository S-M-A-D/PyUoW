import typing as t
from abc import ABC
from dataclasses import dataclass

from ...context import BaseContext
from ...datapoint import (
    BaseDataPointConsumer,
    BaseDataPointContainer,
    BaseDataPointProducer,
    BaseDataPointSpec,
)
from ..base import BaseParams

PARAMS = t.TypeVar("PARAMS", bound=BaseParams)


DATA_POINT_CONTAINER = t.TypeVar(
    "DATA_POINT_CONTAINER", bound=BaseDataPointContainer[t.Any]
)


@dataclass(frozen=True)
class BaseDataPointProducerContext(
    t.Generic[PARAMS, DATA_POINT_CONTAINER],
    BaseContext[PARAMS],
    BaseDataPointProducer[DATA_POINT_CONTAINER],
    ABC,
):
    pass


DATA_POINT_SPEC = t.TypeVar("DATA_POINT_SPEC", bound=BaseDataPointSpec[t.Any])


@dataclass(frozen=True)
class BaseDataPointConsumerContext(
    t.Generic[PARAMS, DATA_POINT_SPEC],
    BaseContext[PARAMS],
    BaseDataPointConsumer[DATA_POINT_SPEC],
    ABC,
):
    pass


@dataclass(frozen=True)
class BaseDataPointContext(
    t.Generic[PARAMS, DATA_POINT_CONTAINER, DATA_POINT_SPEC],
    BaseDataPointProducerContext[PARAMS, DATA_POINT_CONTAINER],
    BaseDataPointConsumerContext[PARAMS, DATA_POINT_SPEC],
    ABC,
):
    pass
