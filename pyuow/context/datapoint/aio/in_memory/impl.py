import typing as t
from dataclasses import dataclass, field

from .....datapoint import (
    BaseDataPointContainer,
    BaseDataPointsDict,
    BaseDataPointSpec,
    DataPointCannotBeOverriddenError,
    DataPointIsNotProducedError,
)
from ..base import BaseDataPointContext, BaseParams

PARAMS = t.TypeVar("PARAMS", bound=BaseParams)


@dataclass(frozen=True)
class InMemoryDataPointContext(
    BaseDataPointContext[
        PARAMS, BaseDataPointContainer[t.Any], BaseDataPointSpec[t.Any]
    ]
):
    params: PARAMS

    _storage: t.Dict[BaseDataPointSpec[t.Any], t.Any] = field(
        init=False, repr=False, default_factory=BaseDataPointsDict
    )

    async def add(self, *datapoints: BaseDataPointContainer[t.Any]) -> None:
        for datapoint in datapoints:
            if datapoint.spec in self._storage:
                raise DataPointCannotBeOverriddenError(datapoint.spec)
            else:
                self._storage[datapoint.spec] = datapoint.value

    async def get(
        self, *specs: BaseDataPointSpec[t.Any]
    ) -> t.Dict[BaseDataPointSpec[t.Any], t.Any]:
        missing = {name for name in specs if name not in self._storage}

        if len(missing) > 0:
            raise DataPointIsNotProducedError(missing)

        return {k: v for k, v in self._storage.items() if k in specs}
