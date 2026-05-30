import typing as t
from dataclasses import dataclass

from ..types import MISSING, MissingType
from .exceptions import MissingOutError

OUT = t.TypeVar("OUT")
NEW = t.TypeVar("NEW")


@dataclass(frozen=True, repr=False)
@t.final
class Result(t.Generic[OUT]):
    _out: t.Union[OUT, MissingType, Exception]

    def get(self) -> OUT:
        self.raise_for_error()
        return t.cast(OUT, self._out)

    def raise_for_error(self) -> None:
        if isinstance(self._out, MissingType):
            raise MissingOutError()
        elif isinstance(self._out, Exception):
            raise self._out

    def is_ok(self) -> bool:
        return not (self.is_error() or self.is_empty())

    def is_empty(self) -> bool:
        return isinstance(self._out, MissingType)

    def is_error(self) -> bool:
        return isinstance(self._out, Exception)

    def map(self, fn: t.Callable[[OUT], NEW]) -> "Result[NEW]":
        if isinstance(self._out, (MissingType, Exception)):
            return t.cast("Result[NEW]", self)
        return Result.ok(fn(self._out))

    def and_then(self, fn: t.Callable[[OUT], "Result[NEW]"]) -> "Result[NEW]":
        if isinstance(self._out, (MissingType, Exception)):
            return t.cast("Result[NEW]", self)
        return fn(self._out)

    def unwrap_or(self, default: OUT) -> OUT:
        if isinstance(self._out, (MissingType, Exception)):
            return default
        return self._out

    @staticmethod
    def ok(out: OUT) -> "Result[OUT]":
        return Result(out)

    @staticmethod
    def error(exc: Exception) -> "Result[OUT]":
        return Result(exc)

    @staticmethod
    def empty() -> "Result[OUT]":
        return Result(MISSING)

    def __repr__(self) -> str:
        if isinstance(self._out, MissingType):
            return "Result.empty()"
        if isinstance(self._out, Exception):
            return f"Result.error({self._out!r})"
        return f"Result.ok({self._out!r})"
