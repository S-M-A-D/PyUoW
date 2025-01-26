import typing as t
from dataclasses import dataclass

from .exceptions import AttributeCannotBeOverriddenError

PARAMS = t.TypeVar("PARAMS", bound="BaseParams")


@dataclass(frozen=True)
class BaseParams:
    pass


class BaseContext(t.Protocol[PARAMS]):
    params: PARAMS


@dataclass
class BaseMutableContext(BaseContext[PARAMS]):
    params: PARAMS

    def __setattr__(self, name: str, value: t.Any) -> None:
        if hasattr(self, name):
            raise AttributeCannotBeOverriddenError(name)

        super().__setattr__(name, value)


@dataclass(frozen=True)
class BaseImmutableContext(BaseContext[PARAMS]):
    params: PARAMS
