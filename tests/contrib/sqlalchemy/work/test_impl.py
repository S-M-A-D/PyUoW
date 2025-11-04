from unittest.mock import Mock

import pytest
from sqlalchemy.engine import Engine

from pyuow.contrib.sqlalchemy.work import (
    SqlAlchemyTransaction,
    SqlAlchemyTransactionManager,
)


@pytest.mark.skip_on_ci
class TestSqlAlchemyTransaction:
    def test_async_rollback_should_call_nested_transaction_rollback(
        self,
    ) -> None:
        # given
        nested_trx = Mock()
        trx_provider = Mock(
            in_nested_transaction=Mock(return_value=True),
            get_nested_transaction=Mock(return_value=nested_trx),
        )
        trx = SqlAlchemyTransaction(trx_provider)
        # when
        trx.rollback()
        # then
        nested_trx.rollback.assert_called_once()

    def test_async_rollback_should_call_root_transaction_rollback(
        self,
    ) -> None:
        # given
        root_trx = Mock()
        trx_provider = Mock(
            in_nested_transaction=Mock(return_value=False),
            in_transaction=Mock(return_value=True),
            get_transaction=Mock(return_value=root_trx),
        )
        trx = SqlAlchemyTransaction(trx_provider)
        # when
        trx.rollback()
        # then
        root_trx.rollback.assert_called_once()

    def test_async_commit_should_call_nested_transaction_commit(
        self,
    ) -> None:
        # given
        nested_trx = Mock()
        trx_provider = Mock(
            in_nested_transaction=Mock(return_value=True),
            get_nested_transaction=Mock(return_value=nested_trx),
        )
        trx = SqlAlchemyTransaction(trx_provider)
        # when
        trx.commit()
        # then
        nested_trx.commit.assert_called_once()

    def test_async_commit_should_call_root_transaction_commit(
        self,
    ) -> None:
        # given
        root_trx = Mock()
        trx_provider = Mock(
            in_nested_transaction=Mock(return_value=False),
            in_transaction=Mock(return_value=True),
            get_transaction=Mock(return_value=root_trx),
        )
        trx = SqlAlchemyTransaction(trx_provider)
        # when
        trx.commit()
        # then
        root_trx.commit.assert_called_once()


@pytest.mark.skip_on_ci
class TestSqlAlchemyTransactionManager:
    def test_transaction_should_return_same_session_if_called_in_already_opened_transaction(
        self, engine: Engine
    ) -> None:
        # given
        manager = SqlAlchemyTransactionManager(engine)
        # when
        with manager.transaction() as trx:
            first_trx = trx.it().get_transaction()

            with manager.transaction() as trx:
                second_trx = trx.it().get_transaction()
        # then
        assert first_trx == second_trx

    def test_transaction_should_return_different_session_if_called_in_already_opened_transaction(
        self, engine: Engine
    ) -> None:
        # given
        manager = SqlAlchemyTransactionManager(engine)
        # when
        with manager.transaction() as trx:
            first_trx = trx.it().get_transaction()

        with manager.transaction() as trx:
            second_trx = trx.it().get_transaction()
        # then
        assert first_trx != second_trx
