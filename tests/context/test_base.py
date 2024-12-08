from dataclasses import dataclass

import pytest

from pyuow.context import (
    AttributeCannotBeOverriddenError,
    BaseMutableContext,
    BaseParams,
)


@dataclass(frozen=True)
class FakeParams(BaseParams):
    pass


@dataclass
class FakeContext(BaseMutableContext[FakeParams]):
    context_field: str


class TestBaseMutableContext:
    def test_should_raise_on_attribute_override(self) -> None:
        # given
        context = FakeContext(params=FakeParams(), context_field="test")
        # when / then
        with pytest.raises(AttributeCannotBeOverriddenError):
            context.context_field = "something"
