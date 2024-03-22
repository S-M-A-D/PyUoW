import typing as t
from dataclasses import dataclass
from unittest.mock import AsyncMock, Mock

import pytest

from pyuow import (
    BaseContext,
    BaseUnit,
    CannotReassignUnitError,
    ConditionalUnit,
    ErrorUnit,
    FinalUnit,
    FinalUnitError,
    Result,
    RunUnit,
)
from pyuow.types import MISSING


class TestUnits:
    async def test_unit_rshift_should_properly_assign_units(
        self,
    ):
        # given
        class FakeUnit(BaseUnit[Mock, None]):
            async def __call__(
                self, context: Mock, **kwargs: t.Any
            ) -> Result[None]:
                pass

        unit1 = FakeUnit()
        unit2 = FakeUnit()
        # when
        unit1 >> unit2
        # then
        assert unit1._root == unit1
        assert unit1._next == unit2
        assert unit2._root == unit1
        assert unit2._next == MISSING

    async def test_unit_rshift_should_raise_on_unit_reassignment(
        self,
    ):
        # given
        class FakeUnit(BaseUnit[Mock, None]):
            async def __call__(
                self, context: Mock, **kwargs: t.Any
            ) -> Result[None]:
                pass

        unit1 = FakeUnit()
        unit2 = FakeUnit()
        # when
        with pytest.raises(CannotReassignUnitError):
            unit1 >> unit2 >> unit1

    async def test_unit_build_should_return_flow_root(
        self,
    ):
        # given
        class FakeUnit(BaseUnit[Mock, None]):
            async def __call__(
                self, context: Mock, **kwargs: t.Any
            ) -> Result[None]:
                pass

        unit1 = FakeUnit()
        unit2 = FakeUnit()
        # when
        flow = unit1 >> unit2
        # then
        assert flow.build() == unit1

    async def test_complex_units_flow_should_behave_properly(self):
        # given
        @dataclass
        class FakeParams:
            pass

        @dataclass
        class FakeContext(BaseContext[FakeParams]):
            context_field: str

        @dataclass(frozen=True)
        class FakeOut:
            result_field: str

        class FakeConditionalUnit(ConditionalUnit[FakeContext, FakeOut]):
            async def condition(
                self, context: FakeContext, **kwargs: t.Any
            ) -> bool:
                return context.context_field == "test"

        class FakeRunUnit(RunUnit[FakeContext, FakeOut]):
            async def run(
                self, context: FakeContext, **kwargs: t.Any
            ) -> None: ...

        class SuccessUnit(FinalUnit[FakeContext, FakeOut]):
            async def finish(
                self, context: FakeContext, **kwargs: t.Any
            ) -> Result[FakeOut]:
                return Result.ok(FakeOut(result_field="success"))

        # when
        flow = (
            FakeConditionalUnit(on_failure=ErrorUnit(exc=Exception("test")))
            >> FakeRunUnit()
            >> SuccessUnit()
        ).build()

        fake_params = FakeParams()
        passed_context = FakeContext(params=fake_params, context_field="test")
        failed_context = FakeContext(
            params=fake_params, context_field="qwerty"
        )
        # then
        passed_result = await flow(passed_context)
        failed_result = await flow(failed_context)
        # then
        assert passed_result.get() == FakeOut(result_field="success")
        assert failed_result.is_error() is True

    async def test_conditional_unit_should_behave_properly(self):
        # given
        class FakeContext(BaseContext[Mock]):
            context_field: str

            def __init__(self, params: Mock, *, context_field: str):
                super().__init__(params)
                self.context_field = context_field

        class FakeConditionalUnit(ConditionalUnit[FakeContext, None]):
            async def condition(
                self, context: FakeContext, **kwargs: t.Any
            ) -> bool:
                return context.context_field == "test"

        mock_params = Mock()
        passed_context = FakeContext(params=mock_params, context_field="test")
        failed_context = FakeContext(
            params=mock_params, context_field="qwerty"
        )
        unit = FakeConditionalUnit(on_failure=Mock())
        # then
        passed_condition = await unit.condition(passed_context)
        failed_condition = await unit.condition(failed_context)
        # then
        assert passed_condition is True
        assert failed_condition is False

    async def test_conditional_unit_in_flow_should_raise_if_next_unit_is_not_set(
        self,
    ):
        # given
        class FakeUnit(ConditionalUnit[Mock, None]):
            async def condition(self, context: Mock, **kwargs: t.Any) -> bool:
                return False

        flow = FakeUnit(on_failure=Mock()).build()
        # when
        with pytest.raises(NotImplementedError):
            await flow(Mock())

    async def test_conditional_unit_in_flow_should_return_result_when_error_occurs(
        self,
    ):
        # given
        class FakeUnit(ConditionalUnit[Mock, None]):
            async def condition(self, context: Mock, **kwargs: t.Any) -> bool:
                raise Exception

        flow = (
            FakeUnit(on_failure=Mock()) >> FakeUnit(on_failure=Mock())
        ).build()
        # when
        result = await flow(Mock())
        # then
        assert result.is_error() is True

    async def test_conditional_unit_in_flow_should_call_failure_if_condition_failed(
        self,
    ):
        # given
        mock_context = Mock()
        mock_on_failure = AsyncMock()

        class FakeUnit(ConditionalUnit[Mock, None]):
            async def condition(self, context: Mock, **kwargs: t.Any) -> bool:
                return False

        flow = (
            FakeUnit(on_failure=mock_on_failure) >> FakeUnit(on_failure=Mock())
        ).build()
        # when
        await flow(mock_context)
        # then
        mock_on_failure.assert_called_once_with(mock_context)

    async def test_run_unit_should_behave_properly(self):
        # given
        mock_context = Mock()
        mock_logic = Mock()

        class FakeUnit(RunUnit[Mock, None]):
            async def run(self, context: Mock, **kwargs: t.Any) -> None:
                mock_logic(context)

        unit = FakeUnit()
        # when
        await unit.run(mock_context)
        # then
        mock_logic.assert_called_once_with(mock_context)

    async def test_run_unit_in_flow_should_raise_if_next_unit_is_not_set(self):
        # given
        class FakeUnit(RunUnit[Mock, None]):
            async def run(self, context: Mock, **kwargs: t.Any) -> None: ...

        flow = FakeUnit().build()
        # when
        with pytest.raises(NotImplementedError):
            await flow(Mock())

    async def test_run_unit_in_flow_should_return_result_when_error_occurs(
        self,
    ):
        # given
        class FakeUnit(RunUnit[Mock, None]):
            async def run(self, context: Mock, **kwargs: t.Any) -> None:
                raise Exception

        flow = (FakeUnit() >> FakeUnit()).build()
        # when
        result = await flow(Mock())
        # then
        assert result.is_error() is True

    async def test_final_unit_should_raise_on_next_assigned(self):
        # given
        class FakeUnit(FinalUnit[Mock, None]):
            async def finish(
                self, context: Mock, **kwargs: t.Any
            ) -> Result[None]:
                return Result.empty()

        # when
        with pytest.raises(FinalUnitError):
            FakeUnit() >> FakeUnit()

    async def test_error_unit_should_behave_properly(self):
        # given
        mock_context = Mock()
        unit = ErrorUnit(exc=Exception("test"))
        # when
        result = await unit.finish(mock_context)
        # then
        assert result.is_error() is True
        mock_context.assert_not_called()
