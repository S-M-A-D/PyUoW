import asyncio
from asyncio import AbstractEventLoop
from pathlib import Path

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

TEST_DB_SCHEMA = Path(__file__).parent / "test_db_schema.sql"


@pytest.fixture(scope="package")
def event_loop() -> AbstractEventLoop:
    loop = asyncio.get_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="package", autouse=True)
async def migrated_db(engine: AsyncEngine) -> None:
    async with engine.connect() as conn, conn.begin():
        await conn.execute(text(TEST_DB_SCHEMA.read_text(encoding="utf-8")))
