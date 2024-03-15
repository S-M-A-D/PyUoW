from dataclasses import dataclass

import pytest

from pyuow import AttributeCannotBeOverriddenError, BaseContext


class TestContext:
    async def test_context_should_raise_if_attribute_on_attr_override(self):
        # given
        @dataclass
        class FakeParams:
            pass

        @dataclass
        class FakeContext(BaseContext[FakeParams]):
            context_field: str

        context = FakeContext(params=FakeParams(), context_field="test")
        # when
        with pytest.raises(AttributeCannotBeOverriddenError):
            context.context_field = "something"
