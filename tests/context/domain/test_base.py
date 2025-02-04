from dataclasses import dataclass
from uuid import uuid4

from pyuow.context import BaseParams
from pyuow.context.domain import BaseDomainContext
from tests.fake_entities import FakeEntity, FakeEntityId


@dataclass(frozen=True)
class FakeParams(BaseParams):
    pass


@dataclass(frozen=True)
class FakeContext(BaseDomainContext[FakeParams]): ...


class TestBaseDomainContext:
    def test_multiple_contexts_do_not_share_same_batch(self) -> None:
        # given
        fake_entity = FakeEntity(
            id=FakeEntityId(uuid4()),
            field="test",
        )
        context_one = FakeContext(
            params=FakeParams(),
        )
        context_one.batch.add(fake_entity)
        context_two = FakeContext(
            params=FakeParams(),
        )
        # when / then
        assert context_one.batch != context_two.batch
