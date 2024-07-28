from unittest.mock import Mock

import pytest
from sqlalchemy.engine import Engine

from pyuow.contrib.sqlalchemy.work import (
    SqlAlchemyTransaction,
    SqlAlchemyTransactionManager,
)


class TestSqlAlchemyTransaction:
    def test_rollback_should_call_transaction_provider_original_rollback(
        self,
    ):
        # given
        trx_provider = Mock()
        trx = SqlAlchemyTransaction(trx_provider)
        # when
        trx.rollback()
        # then
        trx_provider.rollback.assert_called_once()

    def test_commit_should_call_transaction_provider_original_commit(
        self,
    ):
        # given
        trx_provider = Mock()
        trx = SqlAlchemyTransaction(trx_provider)
        # when
        trx.commit()
        # then
        trx_provider.commit.assert_called_once()


@pytest.mark.skip_on_ci
class TestSqlAlchemyTransactionManager:
    def test_transaction_should_return_same_session_if_called_in_already_opened_transaction(
        self, engine: Engine
    ):
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
    ):
        # given
        manager = SqlAlchemyTransactionManager(engine)
        # when
        with manager.transaction() as trx:
            first_trx = trx.it().get_transaction()

        with manager.transaction() as trx:
            second_trx = trx.it().get_transaction()
        # then
        assert first_trx != second_trx
