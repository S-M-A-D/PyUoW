import typing as t

from ... import BaseUnit, Result
from ...result import OUT
from ...units import CONTEXT
from ...work import BaseWorkManager, BaseWorkProxy
from ...work.transactional import BaseTransactionManager
from ...work.transactional.base import TRANSACTION


class TransactionalWorkProxy(BaseWorkProxy):
    def __init__(
        self,
        *,
        transaction_manager: BaseTransactionManager[TRANSACTION],
        unit: BaseUnit[CONTEXT, OUT],
    ) -> None:
        self._transaction_manager = transaction_manager
        self._unit = unit

    async def do_with(self, context: t.Any, **kwargs: t.Any) -> Result[t.Any]:
        async with self._transaction_manager.transaction() as trx:
            result = await self._unit(context, **kwargs)

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

    def by(self, unit: BaseUnit[CONTEXT, OUT]) -> BaseWorkProxy:
        return TransactionalWorkProxy(
            transaction_manager=self._transaction_manager,
            unit=unit,
        )
