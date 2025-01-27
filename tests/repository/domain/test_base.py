from unittest.mock import Mock
from uuid import uuid4

from pyuow.domain import Batch
from pyuow.repository.domain import BaseDomainRepository
from tests.fake_entities import FakeEntity, FakeEntityId, FakeModel


class TestBaseDomainRepository:
    async def test_process_batch_should_properly_direct_changes_and_handle_events(
        self,
    ) -> None:
        # given
        add_mock = Mock()
        update_mock = Mock()
        delete_mock = Mock()
        factory_mock = Mock(
            repo_for=lambda *_, **__: Mock(
                add=add_mock, update=update_mock, delete=delete_mock
            )
        )
        events_handler_mock = Mock()
        repository = BaseDomainRepository(
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
        repository.process_batch(batch)
        # then
        add_mock.assert_called_with(add_entity)
        update_mock.assert_called_with(update_entity)
        delete_mock.assert_called_with(delete_entity)
        events_handler_mock.assert_called_with(batch.events())
