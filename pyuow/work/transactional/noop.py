import typing as t
from contextlib import asynccontextmanager

from ... import BaseUnit
from ...result import OUT, Result
from ...types import MISSING, MissingType
from ...units import CONTEXT
from ..base import BaseWorkManager, BaseWorkProxy
from .base import (
    TRANSACTION,
    BaseTransaction,
    BaseTransactionManager,
    TransactionalWorkProxy,
)


class NoOpTransaction(BaseTransaction[MissingType]):
    def it(self) -> MissingType:
        return MISSING

    async def rollback(self) -> None:
        pass

    async def commit(self) -> None:
        pass


class NoOpTransactionManager(BaseTransactionManager[NoOpTransaction]):
    @asynccontextmanager
    async def transaction(
        self,
    ) -> t.AsyncIterator[NoOpTransaction]:
        yield NoOpTransaction()


class NoOpWorkProxy(TransactionalWorkProxy):
    def __init__(
        self,
        *,
        transaction_manager: BaseTransactionManager[TRANSACTION],
        unit: BaseUnit[CONTEXT, OUT],
    ) -> None:
        self._transaction_manager = transaction_manager
        self._unit = unit
        super().__init__(transaction_manager=transaction_manager, unit=unit)

    async def do(self, context: t.Any, **kwargs: t.Any) -> Result[t.Any]:
        return await self._unit(context, **kwargs)


class NoOpWorkManager(BaseWorkManager):
    def __init__(
        self,
        *,
        transaction_manager: BaseTransactionManager[TRANSACTION],
    ) -> None:
        self._transaction_manager = transaction_manager

    def by(self, unit: BaseUnit[CONTEXT, OUT]) -> BaseWorkProxy:
        return NoOpWorkProxy(
            transaction_manager=self._transaction_manager, unit=unit
        )
