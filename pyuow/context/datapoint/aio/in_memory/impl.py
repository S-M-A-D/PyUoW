import typing as t
from dataclasses import dataclass, field

from .....datapoint import (
    BaseDataPoint,
    BaseDataPointName,
    DataPointCannotBeOverriddenError,
    DataPointDict,
    DataPointIsNotProducedError,
)
from ..base import BaseDataPointContext, BaseParams

PARAMS = t.TypeVar("PARAMS", bound=BaseParams)


@dataclass(frozen=True)
class InMemoryDataPointContext(BaseDataPointContext[PARAMS]):
    params: PARAMS

    _storage: DataPointDict[t.Any] = field(
        init=False, repr=False, default_factory=DataPointDict
    )

    async def add(
        self, *datapoints: BaseDataPoint[BaseDataPointName[t.Any], t.Any]
    ) -> None:
        for datapoint in datapoints:
            if datapoint.name in self._storage:
                raise DataPointCannotBeOverriddenError(datapoint.name)
            else:
                self._storage[datapoint.name] = datapoint.value

    async def get(
        self, *names: BaseDataPointName[t.Any]
    ) -> DataPointDict[t.Any]:
        missing = {name for name in names if name not in self._storage}

        if len(missing) > 0:
            raise DataPointIsNotProducedError(missing)

        return t.cast(
            DataPointDict[t.Any],
            {k: v for k, v in self._storage.items() if k in names},
        )
