from unittest.mock import AsyncMock, Mock
from uuid import uuid4

from pyuow.domain import Batch
from pyuow.repository.aio.domain import DomainRepository
from tests.fake_entities import FakeEntity, FakeEntityId, FakeModel


class TestBaseDomainRepository:
    async def test_async_process_batch_should_properly_direct_changes_and_handle_events(
        self,
    ) -> None:
        # given
        add_mock = AsyncMock()
        update_mock = AsyncMock()
        delete_mock = AsyncMock()
        factory_mock = Mock(
            repo_for=lambda *_, **__: AsyncMock(
                add=add_mock, update=update_mock, delete=delete_mock
            )
        )
        events_handler_mock = AsyncMock()
        repository = DomainRepository(
            repositories=factory_mock,
            events_handler=events_handler_mock,
        )

        add_entity = FakeModel()
        update_entity = FakeEntity(id=FakeEntityId(uuid4()))
        delete_entity = FakeEntity(id=FakeEntityId(uuid4()))

        batch = Batch()
        batch.add(add_entity)
        batch.update(update_entity)
        batch.delete(delete_entity)
        # when
        await repository.process_batch(batch)
        # then
        add_mock.assert_awaited_once_with(add_entity)
        update_mock.assert_awaited_once_with(update_entity)
        delete_mock.assert_awaited_once_with(delete_entity)
        events_handler_mock.assert_awaited_once_with(batch.events())
