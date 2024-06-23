from time import sleep
from typing import Iterator

import pytest
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from testcontainers.postgres import PostgresContainer


@pytest.fixture(scope="session")
def postgres() -> Iterator[PostgresContainer]:
    with PostgresContainer("postgres:15", driver="asyncpg") as postgres:
        # TODO: fix it
        sleep(5)
        yield postgres


@pytest.fixture(scope="session")
def engine(postgres: PostgresContainer) -> Iterator[AsyncEngine]:
    engine = create_async_engine(
        postgres.get_connection_url(),
        echo=True,
        echo_pool=True,
        pool_pre_ping=True,
    )
    yield engine
