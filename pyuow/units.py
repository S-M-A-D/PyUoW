import abc
import typing as t
from abc import ABC
from logging import getLogger

from .context import BaseContext
from .exceptions import CannotReassignUnitError, \
    FinalUnitError
from .result import Result
from .types import MissingType, MISSING

logger = getLogger(__name__)

CONTEXT = t.TypeVar("CONTEXT", bound=BaseContext[t.Any])
OUT = t.TypeVar("OUT")

class BaseUnit(t.Generic[CONTEXT, OUT], abc.ABC):
    def __init__(self) -> None:
        self._root: "BaseUnit[CONTEXT, OUT]" = self
        self._next: "BaseUnit[CONTEXT, OUT]" | MissingType = MISSING

    @abc.abstractmethod
    async def __call__(
        self, context: CONTEXT, **kwargs: t.Any
    ) -> Result[OUT]:  # pragma: no cover
        ...

    def __rshift__(
        self: "BaseUnit[CONTEXT, OUT]", other: "BaseUnit[CONTEXT, OUT]"
    ) -> "BaseUnit[CONTEXT, OUT]":
        if not isinstance(other._next, MissingType):
            raise CannotReassignUnitError

        self._next = other
        other._root = self._root
        return other

    def build(self) -> "BaseUnit[CONTEXT, OUT]":
        return self._root


class FinalUnit(BaseUnit[CONTEXT, OUT], ABC):
    async def __call__(self, context: CONTEXT, **kwargs: t.Any) -> Result[OUT]:
        result = await self.finish(context, **kwargs)
        logger.info("[%s] completed", self.__class__.__name__)
        logger.debug("[%s] result [%s]", self.__class__.__name__, result)
        return result

    @abc.abstractmethod
    async def finish(
        self, context: CONTEXT, **kwargs: t.Any
    ) -> Result[OUT]:  # pragma: no cover
        ...

    def __rshift__(
        self: "BaseUnit[CONTEXT, OUT]", other: "BaseUnit[CONTEXT, OUT]"
    ) -> "BaseUnit[CONTEXT, OUT]":
        raise FinalUnitError(self.__class__.__name__)

@t.final
class ErrorUnit(FinalUnit[CONTEXT, OUT]):
    def __init__(
        self,
        exc: Exception,
    ) -> None:
        super().__init__()
        self._exc = exc

    async def finish(self, context: CONTEXT, **kwargs: t.Any) -> Result[OUT]:
        return Result.error(self._exc)


class ConditionalUnit(BaseUnit[CONTEXT, OUT]):
    def __init__(self, *, on_failure: BaseUnit[CONTEXT, OUT]) -> None:
        super().__init__()
        self._on_failure = on_failure

    async def __call__(self, context: CONTEXT, **kwargs: t.Any) -> Result[OUT]:
        cls_name = self.__class__.__name__

        if isinstance(self._next, MissingType):
            raise NotImplementedError(f"[{cls_name}] next unit is not set")

        try:
            passed = await self.condition(context, **kwargs)
        except Exception as error:
            logger.exception(
                "[%s] failed with exception", cls_name, exc_info=error
            )
            return Result.error(error)

        if passed:
            logger.info("[%s] completed", cls_name)
            return await self._next(context, **kwargs)

        logger.info("[%s] failed", cls_name)
        return await self._on_failure(context, **kwargs)

    @abc.abstractmethod
    async def condition(
        self, context: CONTEXT, **kwargs: t.Any
    ) -> bool:  # pragma: no cover
        ...


class RunUnit(BaseUnit[CONTEXT, OUT]):
    async def __call__(self, context: CONTEXT, **kwargs: t.Any) -> Result[OUT]:
        cls_name = self.__class__.__name__

        if isinstance(self._next, MissingType):
            raise NotImplementedError(f"[{cls_name}] next unit is not set")

        try:
            await self.run(context, **kwargs)
        except Exception as error:
            logger.exception(
                "[%s] failed with exception", cls_name, exc_info=error
            )
            return Result.error(error)

        logger.info("[%s] completed", cls_name)
        return await self._next(context, **kwargs)

    @abc.abstractmethod
    async def run(
        self, context: CONTEXT, **kwargs: t.Any
    ) -> None:  # pragma: no cover
        ...
