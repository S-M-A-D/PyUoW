from typing import Iterator

import pytest
from sqlalchemy import NullPool
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from testcontainers.postgres import PostgresContainer


@pytest.fixture(scope="session")
def postgres() -> Iterator[PostgresContainer]:
    with PostgresContainer("postgres:15", driver="asyncpg") as postgres:
        yield postgres


@pytest.fixture(scope="session")
def engine(postgres: PostgresContainer) -> Iterator[AsyncEngine]:
    engine = create_async_engine(
        postgres.get_connection_url(),
        # NullPool is required for sqlalchemy in tests
        # to properly work with asyncio
        # https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html#using-multiple-asyncio-event-loops
        poolclass=NullPool,
        echo=True,
        echo_pool=True,
        pool_pre_ping=True,
    )
    yield engine
