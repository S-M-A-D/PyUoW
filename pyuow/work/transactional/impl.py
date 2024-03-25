from ...result import OUT, Result
from ...units import CONTEXT, BaseUnit
from ...work import BaseWorkManager
from ...work.transactional import BaseTransactionManager
from ...work.transactional.base import TRANSACTION
from ..base import BaseUnitProxy


class TransactionalUnitProxy(BaseUnitProxy[CONTEXT, OUT]):
    def __init__(
        self,
        *,
        transaction_manager: BaseTransactionManager[TRANSACTION],
        unit: BaseUnit[CONTEXT, OUT],
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
