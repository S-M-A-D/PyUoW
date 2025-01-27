import typing as t

from ....context import BaseContext
from ....context.domain import BaseDomainContext
from ....domain import Batch
from ....result import Result
from ....unit import BaseUnit
from ....work import BaseUnitProxy
from ....work.transactional import (
    BaseTransactionManager,
    TransactionalWorkManager,
)
from .. import BaseTransaction

CONTEXT = t.TypeVar("CONTEXT", bound=BaseContext[t.Any])
OUT = t.TypeVar("OUT")
TRANSACTION = t.TypeVar("TRANSACTION", bound=BaseTransaction[t.Any])


class DomainUnit(BaseUnit[CONTEXT, OUT]):
    def __init__(
        self,
        *,
        unit: BaseUnit[CONTEXT, OUT],
        batch_handler: t.Callable[[Batch], None],
    ) -> None:
        self._unit = unit
        self._batch_handler = batch_handler

    def __call__(self, context: CONTEXT) -> Result[OUT]:
        result = self._unit(context)

        if isinstance(context, BaseDomainContext):
            self._batch_handler(context.batch)

        return result


class DomainTransactionalWorkManager(TransactionalWorkManager):
    def __init__(
        self,
        *,
        transaction_manager: BaseTransactionManager[TRANSACTION],
        batch_handler: t.Callable[[Batch], None],
    ) -> None:
        super().__init__(transaction_manager=transaction_manager)
        self._batch_handler = batch_handler

    def by(self, unit: BaseUnit[CONTEXT, OUT]) -> BaseUnitProxy[CONTEXT, OUT]:
        return super().by(
            unit=DomainUnit(
                unit=unit,
                batch_handler=self._batch_handler,
            )
        )
