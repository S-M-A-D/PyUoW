from ...result import OUT, Result
from ...units import CONTEXT, BaseAsyncUnit, BaseUnit
from ...work import BaseAsyncWorkManager, BaseWorkManager
from ...work.transactional import (
    BaseAsyncTransactionManager,
    BaseTransactionManager,
)
from ...work.transactional.base import ASYNC_TRANSACTION, TRANSACTION
from ..base import BaseAsyncUnitProxy, BaseUnitProxy


class TransactionalUnitProxy(BaseUnitProxy[CONTEXT, OUT]):
    def __init__(
        self,
        *,
        transaction_manager: BaseTransactionManager[TRANSACTION],
        unit: BaseUnit[CONTEXT, OUT],
    ) -> None:
        self._transaction_manager = transaction_manager
        self._unit = unit

    def __call__(self, context: CONTEXT) -> Result[OUT]:
        with self._transaction_manager.transaction() as trx:
            result = self._unit(context)

            if result.is_error():
                trx.rollback()
            else:
                trx.commit()

            return result


class TransactionalAsyncUnitProxy(BaseAsyncUnitProxy[CONTEXT, OUT]):
    def __init__(
        self,
        *,
        transaction_manager: BaseAsyncTransactionManager[ASYNC_TRANSACTION],
        unit: BaseAsyncUnit[CONTEXT, OUT],
    ) -> None:
        self._transaction_manager = transaction_manager
        self._unit = unit

    async def __call__(self, context: CONTEXT) -> Result[OUT]:
        async with self._transaction_manager.transaction() as trx:
            result = await self._unit(context)

            if result.is_error():
                await trx.rollback()
            else:
                await trx.commit()

            return result


class TransactionalWorkManager(BaseWorkManager):
    def __init__(
        self,
        *,
        transaction_manager: BaseTransactionManager[TRANSACTION],
    ) -> None:
        self._transaction_manager = transaction_manager

    def by(self, unit: BaseUnit[CONTEXT, OUT]) -> BaseUnitProxy[CONTEXT, OUT]:
        return TransactionalUnitProxy(
            transaction_manager=self._transaction_manager,
            unit=unit,
        )


class TransactionalAsyncWorkManager(BaseAsyncWorkManager):
    def __init__(
        self,
        *,
        transaction_manager: BaseAsyncTransactionManager[ASYNC_TRANSACTION],
    ) -> None:
        self._transaction_manager = transaction_manager

    def by(
        self, unit: BaseAsyncUnit[CONTEXT, OUT]
    ) -> BaseAsyncUnitProxy[CONTEXT, OUT]:
        return TransactionalAsyncUnitProxy(
            transaction_manager=self._transaction_manager,
            unit=unit,
        )
