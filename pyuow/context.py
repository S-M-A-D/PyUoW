import typing as t
from dataclasses import dataclass

from .exceptions import AttributeCannotBeOverriddenError

PARAMS = t.TypeVar("PARAMS")


@dataclass
class BaseContext(t.Generic[PARAMS]):
    params: PARAMS

    def __setattr__(self, name: str, value: t.Any) -> None:
        if hasattr(self, name):
            raise AttributeCannotBeOverriddenError(name)

        super().__setattr__(name, value)

