import typing as t

from ...context import BaseContext
from ...result import Result
from ...unit import BaseUnit
from ...work import BaseWorkManager
from ...work.transactional import BaseTransaction, BaseTransactionManager
from ..base import BaseUnitProxy

CONTEXT = t.TypeVar("CONTEXT", bound=BaseContext[t.Any])
OUT = t.TypeVar("OUT")
TRANSACTION = t.TypeVar("TRANSACTION", bound=BaseTransaction[t.Any])


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
