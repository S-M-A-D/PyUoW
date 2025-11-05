from unittest.mock import Mock

import pytest
from sqlalchemy.engine import Engine

from pyuow.contrib.sqlalchemy.work import (
    SqlAlchemyTransaction,
    SqlAlchemyTransactionManager,
)


@pytest.mark.skip_on_ci
class TestSqlAlchemyTransaction:
    def test_sync_rollback_should_call_nested_transaction_rollback(
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

    def test_sync_rollback_should_call_root_transaction_rollback(
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

    def test_sync_commit_should_call_nested_transaction_commit(
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

    def test_sync_commit_should_call_root_transaction_commit(
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
    def test_sync_transaction_should_open_nested_transaction_if_called_in_already_opened_transaction(
        self, engine: Engine
    ) -> None:
        # given
        manager = SqlAlchemyTransactionManager(engine)
        # when
        with manager.transaction() as trx:
            first_session = trx.it()

            with manager.transaction() as trx2:
                second_session = trx2.it()

                # then
                assert first_session.in_transaction()
                assert second_session.in_nested_transaction()

            assert first_session.in_transaction()
            assert not second_session.in_nested_transaction()

        assert not first_session.in_transaction()

    def test_sync_transaction_should_not_open_nested_transaction_if_called_in_new_transaction(
        self, engine: Engine
    ) -> None:
        # given
        manager = SqlAlchemyTransactionManager(engine)
        # when
        with manager.transaction() as trx:
            session = trx.it()

            # then
            assert session.in_transaction()
            assert not session.in_nested_transaction()

        assert not session.in_transaction()
