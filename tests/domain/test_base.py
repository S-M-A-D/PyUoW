from __future__ import annotations

import datetime
import typing as t
from unittest.mock import ANY
from uuid import UUID, uuid4

import pytest

from pyuow.domain import Batch, Change, ChangeType
from pyuow.entity import Entity, Version
from tests.fake_entities import (
    FakeEntity,
    FakeEntityId,
    FakeModel,
    FakeModelCreatedEvent,
    FakeModelDeletedEvent,
    FakeModelId,
    FakeModelUpdatedEvent,
)


class TestModel:
    def test_post_init_should_properly_set_defaults_when_id_is_not_provided(
        self,
    ) -> None:
        # given
        model = FakeModel(field="test")
        # when / then
        assert model.field == "test"
        assert isinstance(model.id, UUID)
        assert model.version == Version(0)
        assert model.created_date == model.updated_date
        assert model.deleted_date is None
        assert model.is_new
        assert not model.is_deleted
        assert model.events() == [
            FakeModelCreatedEvent(
                id=ANY,
                model_id=model.id,
                field="test",
                created_date=model.created_date,
            )
        ]

    def test_post_init_should_properly_set_defaults_when_id_is_provided(
        self,
    ) -> None:
        # given
        model_id = FakeModelId(uuid4())
        model = FakeModel(id=model_id, field="test")
        # when / then
        assert model.field == "test"
        assert isinstance(model.id, UUID)
        assert model.version == Version(0)
        assert model.created_date == model.updated_date
        assert model.deleted_date is None
        assert not model.is_new
        assert not model.is_deleted
        assert model.events() == []

    def test_events_contain_all_events_history(self) -> None:
        # given
        model = FakeModel(field="test")
        # when
        changed_model = model.change_field("change 1").change_field("change 2")
        # then
        first, second, third = changed_model.events()
        assert first == FakeModelCreatedEvent(
            id=ANY,
            model_id=changed_model.id,
            field="test",
            created_date=changed_model.created_date,
        )
        assert second == FakeModelUpdatedEvent(
            id=ANY, model_id=changed_model.id, new_field="change 1"
        )
        assert third == FakeModelUpdatedEvent(
            id=ANY, model_id=changed_model.id, new_field="change 2"
        )

    def test_delete_should_set_deleted_date_and_add_an_event_to_history(
        self,
    ) -> None:
        # given
        model_id = FakeModelId(uuid4())
        model = FakeModel(id=model_id, field="test")
        # when
        deleted_model = model.delete()
        # then
        assert deleted_model.is_deleted
        assert deleted_model.deleted_date is not None
        (first,) = deleted_model.events()
        assert first == FakeModelDeletedEvent(
            id=ANY,
            model_id=deleted_model.id,
            deleted_date=deleted_model.deleted_date,
        )

    def test_update_should_create_a_new_instance_and_add_an_event_to_history(
        self,
    ) -> None:
        # given
        model_id = FakeModelId(uuid4())
        model = FakeModel(id=model_id, field="test")
        # when
        changed_model = model.change_field("change 1")
        # then
        assert model != changed_model
        (first,) = changed_model.events()
        assert first == FakeModelUpdatedEvent(
            id=ANY, model_id=model.id, new_field="change 1"
        )


class TestBatch:
    @pytest.mark.parametrize(
        "entity",
        (
            (FakeModel()),
            (FakeEntity(id=FakeEntityId(uuid4()))),
        ),
    )
    def test_add_should_add_entity_to_change_log(
        self, entity: Entity[t.Any]
    ) -> None:
        # given
        batch = Batch()
        # when
        batch.add(entity)
        # then
        assert batch.changes() == {
            entity.id: Change(type=ChangeType.ADD, entity=entity),
        }

    def test_add_should_raise_if_model_is_not_new(self) -> None:
        # given
        old_model = FakeModel(id=FakeModelId(uuid4()))
        batch = Batch()
        # when / then
        with pytest.raises(RuntimeError, match="Can't add an existing entity"):
            batch.add(old_model)

    @pytest.mark.parametrize(
        "entity",
        (
            (FakeModel(id=FakeModelId(uuid4()))),
            (FakeEntity(id=FakeEntityId(uuid4()))),
        ),
    )
    def test_update_should_add_entity_to_change_log(
        self, entity: Entity[t.Any]
    ) -> None:
        # given
        batch = Batch()
        # when
        batch.update(entity)
        # then
        assert batch.changes() == {
            entity.id: Change(type=ChangeType.UPDATE, entity=entity),
        }

    def test_update_should_raise_if_model_is_new(self) -> None:
        # given
        new_model = FakeModel()
        batch = Batch()
        # when / then
        with pytest.raises(RuntimeError, match="Can't update a new entity"):
            batch.update(new_model)

    @pytest.mark.parametrize(
        "entity",
        (
            (FakeModel(id=FakeModelId(uuid4()))),
            (FakeEntity(id=FakeEntityId(uuid4()))),
        ),
    )
    def test_delete_should_add_entity_to_change_log(
        self, entity: Entity[t.Any]
    ) -> None:
        # given
        batch = Batch()
        # when
        batch.delete(entity)
        # then
        assert batch.changes() == {
            entity.id: Change(type=ChangeType.DELETE, entity=entity),
        }

    def test_delete_should_raise_if_model_is_new(self) -> None:
        # given
        new_model = FakeModel()
        batch = Batch()
        # when / then
        with pytest.raises(RuntimeError, match="Can't delete a new entity"):
            batch.delete(new_model)

    def test_change_should_raise_if_batch_is_shut(self) -> None:
        # given
        model = FakeModel()
        batch = Batch()
        batch.shut()
        # when / then
        with pytest.raises(
            RuntimeError, match="Batch can't be changed, it's already shut"
        ):
            batch.add(model)

    def test_change_should_raise_if_entity_already_in_batch(self) -> None:
        # given
        model_id = FakeModelId(uuid4())
        model = FakeModel(id=model_id)
        batch = Batch()
        batch.update(model)
        # when / then
        with pytest.raises(
            RuntimeError,
            match=f"{model.__class__.__name__}\[{model.id}\] has already been added to batch with UPDATE operation",
        ):
            batch.delete(model)

    def test_events_should_return_all_events_from_all_entities_in_batch(
        self,
    ) -> None:
        # given
        created_model = FakeModel(field="test")
        updated_model = FakeModel(id=FakeModelId(uuid4())).change_field(
            "change 1"
        )
        deleted_model = FakeModel(id=FakeModelId(uuid4())).delete()
        batch = Batch()
        # when
        batch.add(created_model)
        batch.update(updated_model)
        batch.delete(deleted_model)
        # then
        assert batch.events() == [
            FakeModelCreatedEvent(
                id=ANY,
                model_id=created_model.id,
                created_date=created_model.created_date,
                field="test",
            ),
            FakeModelUpdatedEvent(
                id=ANY,
                model_id=updated_model.id,
                new_field="change 1",
            ),
            FakeModelDeletedEvent(
                id=ANY,
                model_id=deleted_model.id,
                deleted_date=t.cast(
                    datetime.datetime, deleted_model.deleted_date
                ),
            ),
        ]
