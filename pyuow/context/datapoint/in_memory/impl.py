import typing as t
from dataclasses import dataclass, field

from ....datapoint import BaseDataPoint, BaseDataPointName, DataPointDict
from ....exceptions import (
    DataPointCannotBeOverriddenError,
    DataPointIsNotProducedError,
)
from .. import BaseDataPointContext
from ..base import PARAMS


@dataclass(frozen=True)
class InMemoryDataPointContext(BaseDataPointContext[PARAMS]):
    params: PARAMS

    _storage: DataPointDict[t.Any] = field(
        init=False, repr=False, default_factory=DataPointDict
    )

    def add(
        self, *datapoints: BaseDataPoint[BaseDataPointName[t.Any], t.Any]
    ) -> None:
        for datapoint in datapoints:
            if datapoint.name in self._storage:
                raise DataPointCannotBeOverriddenError(datapoint.name)
            else:
                self._storage[datapoint.name] = datapoint.value

    def get(self, *names: BaseDataPointName[t.Any]) -> DataPointDict[t.Any]:
        missing = {name for name in names if name not in self._storage}

        if len(missing) > 0:
            raise DataPointIsNotProducedError(missing)

        return t.cast(
            DataPointDict[t.Any],
            {k: v for k, v in self._storage.items() if k in names},
        )
