import typing as t
from contextlib import contextmanager

try:
    from sqlalchemy import Engine
    from sqlalchemy.orm import Session, scoped_session, sessionmaker
except ImportError:  # pragma: no cover
    raise ImportError(
        "Seems that you are trying to import extra module that was not installed,"
        " please install pyuow[sqlalchemy]"
    )

from ....work.transactional import BaseTransaction, BaseTransactionManager


class SqlAlchemyTransaction(BaseTransaction[Session]):
    def rollback(self) -> None:
        self._transaction_provider.rollback()

    def commit(self) -> None:
        self._transaction_provider.commit()


class SqlAlchemyTransactionManager(
    BaseTransactionManager[SqlAlchemyTransaction]
):
    def __init__(self, engine: Engine) -> None:
        self._session_factory = scoped_session(
            sessionmaker(engine, expire_on_commit=False)
        )

    @contextmanager
    def transaction(self) -> t.Iterator[SqlAlchemyTransaction]:
        session = self._session_factory()
        if session.in_transaction():
            yield SqlAlchemyTransaction(session)
        else:
            with session.begin():
                yield SqlAlchemyTransaction(session)


class SqlAlchemyReadOnlyTransactionManager(SqlAlchemyTransactionManager):
    def __init__(self, engine: Engine) -> None:
        super().__init__(
            engine.execution_options(isolation_level="AUTOCOMMIT")
        )

    @contextmanager
    def transaction(self) -> t.Iterator[SqlAlchemyTransaction]:
        with self._session_factory() as session:
            yield SqlAlchemyTransaction(session)
