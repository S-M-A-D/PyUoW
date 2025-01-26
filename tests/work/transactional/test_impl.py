import typing as t
from contextlib import contextmanager
from dataclasses import dataclass
from unittest.mock import Mock

from pyuow.context import BaseImmutableContext, BaseParams
from pyuow.context.domain import BaseDomainContext
from pyuow.result import Result
from pyuow.unit import BaseUnit
from pyuow.work.transactional import (
    BaseTransaction,
    BaseTransactionManager,
    TransactionalUnitProxy,
    TransactionalWorkManager,
)
from pyuow.work.transactional.impl import (
    DomainTransactionalWorkManager,
    DomainUnit,
)


@dataclass(frozen=True)
class FakeParams(BaseParams):
    pass


@dataclass(frozen=True)
class FakeSimpleContext(BaseImmutableContext[FakeParams]):
    pass


@dataclass(frozen=True)
class FakeContext(BaseDomainContext[FakeParams], FakeSimpleContext):
    pass


@dataclass(frozen=True)
class FakeOut:
    pass


class SuccessUnit(BaseUnit[FakeContext, FakeOut]):
    def __call__(
        self, context: FakeContext, **kwargs: t.Any
    ) -> Result[FakeOut]:
        return Result.ok(FakeOut())


class FailureUnit(BaseUnit[FakeContext, FakeOut]):
    def __call__(
        self, context: FakeContext, **kwargs: t.Any
    ) -> Result[FakeOut]:
        return Result.error(Exception("Something went wrong"))


class FakeTransaction(BaseTransaction[Mock]):
    def rollback(self) -> None:
        self._transaction_provider.rollback()

    def commit(self) -> None:
        self._transaction_provider.commit()


class FakeTransactionManager(BaseTransactionManager[FakeTransaction]):
    def __init__(self, trx_provider_factory: t.Callable[[], Mock]):
        self._trx_provider_factory = trx_provider_factory

    @contextmanager
    def transaction(self) -> t.Iterator[FakeTransaction]:
        yield FakeTransaction(self._trx_provider_factory())


class TestTransactionalUnitProxy:
    def test_do_with_should_commit_on_success(self) -> None:
        # given
        unit = SuccessUnit()
        params = FakeParams()
        context = FakeContext(params=params)
        transaction = Mock()
        transaction_manager = FakeTransactionManager(lambda: transaction)
        work_proxy = TransactionalUnitProxy(
            transaction_manager=transaction_manager, unit=unit
        )
        # when
        result = work_proxy.do_with(context=context)
        # then
        assert result.is_ok()
        transaction.commit.assert_called_once()

    def test_do_with_should_rollback_on_error(self) -> None:
        # given
        unit = FailureUnit()
        params = FakeParams()
        context = FakeContext(params=params)
        transaction = Mock()
        transaction_manager = FakeTransactionManager(lambda: transaction)
        work_proxy = TransactionalUnitProxy(
            transaction_manager=transaction_manager, unit=unit
        )
        # when
        result = work_proxy.do_with(context=context)
        # then
        assert result.is_error()
        transaction.rollback.assert_called_once()


class TestTransactionalWorkManager:
    def test_by_should_delegate_unit_to_work_proxy(self) -> None:
        # given
        transaction_manager = Mock(spec=BaseTransactionManager)
        work_manager = TransactionalWorkManager(
            transaction_manager=transaction_manager
        )
        unit = SuccessUnit()
        # when
        proxy = work_manager.by(unit)
        # then
        assert isinstance(proxy, TransactionalUnitProxy)

    def test_example_fake_flow_should_pass(self) -> None:
        # given
        unit = SuccessUnit()
        params = FakeParams()
        context = FakeContext(params=params)
        transaction = Mock()
        transaction_manager = FakeTransactionManager(lambda: transaction)
        work = TransactionalWorkManager(
            transaction_manager=transaction_manager
        )
        # when
        result = work.by(unit).do_with(context)
        # then
        assert result.is_ok()
        assert result.get() == FakeOut()


class TestDomainTransactionalWorkManager:
    def test_by_should_delegate_unit_to_work_proxy(self) -> None:
        # given
        transaction_manager = Mock(spec=BaseTransactionManager)
        batch_handler = Mock()
        work_manager = DomainTransactionalWorkManager(
            transaction_manager=transaction_manager,
            batch_handler=batch_handler,
        )
        unit = SuccessUnit()
        # when
        proxy = work_manager.by(unit)
        # then
        assert isinstance(proxy, TransactionalUnitProxy)

    def test_domain_unit_should_omit_batch_handling_if_context_with_no_batch_provided(
        self,
    ) -> None:
        # given
        params = FakeParams()
        batch_handler = Mock()
        unit = DomainUnit(unit=SuccessUnit(), batch_handler=batch_handler)
        # when
        context = FakeSimpleContext(params=params)
        result = unit(context)  # type: ignore[arg-type]
        # then
        assert result.is_ok()
        batch_handler.assert_not_called()

    def test_example_fake_flow_should_pass(self) -> None:
        # given
        unit = SuccessUnit()
        params = FakeParams()
        context = FakeContext(params=params)
        transaction = Mock()
        transaction_manager = FakeTransactionManager(lambda: transaction)
        batch_handler = Mock()
        work = DomainTransactionalWorkManager(
            transaction_manager=transaction_manager,
            batch_handler=batch_handler,
        )
        # when
        result = work.by(unit).do_with(context)
        # then
        assert result.is_ok()
        assert result.get() == FakeOut()
        batch_handler.assert_called_with(context.batch)
