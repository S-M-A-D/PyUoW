from dataclasses import dataclass

import pytest

from pyuow.context import BaseParams
from pyuow.context.datapoint.in_memory import InMemoryDataPointContext
from pyuow.datapoint import (
    BaseDataPointSpec,
    DataPointCannotBeOverriddenError,
    DataPointIsNotProducedError,
)


@dataclass(frozen=True)
class FakeParams(BaseParams):
    pass


@dataclass(frozen=True)
class FakeComplexType:
    fake_field: int


FakeDatapointOne = BaseDataPointSpec("fake_datapoint_one", FakeComplexType)
FakeDatapointTwo = BaseDataPointSpec("fake_datapoint_two", FakeComplexType)


class TestInMemoryDataPointContext:
    @pytest.fixture
    def params(self) -> FakeParams:
        return FakeParams()

    @pytest.fixture
    def context(
        self, params: FakeParams
    ) -> InMemoryDataPointContext[FakeParams]:
        return InMemoryDataPointContext(params=params)

    def test_should_properly_add_and_get_datapoints(
        self, context: InMemoryDataPointContext[FakeParams]
    ) -> None:
        # given
        complex_obj_one = FakeComplexType(fake_field=123)
        complex_obj_two = FakeComplexType(fake_field=456)
        fake_datapoint_one = FakeDatapointOne(complex_obj_one)
        fake_datapoint_two = FakeDatapointTwo(complex_obj_two)
        # when
        context.add(fake_datapoint_one, fake_datapoint_two)
        # then
        datapoints = context.get(FakeDatapointOne, FakeDatapointTwo)
        assert datapoints[FakeDatapointOne] == complex_obj_one
        assert datapoints[FakeDatapointTwo] == complex_obj_two

    def test_add_should_raise_if_duplicated_datapoint_added(
        self, context: InMemoryDataPointContext[FakeParams]
    ) -> None:
        # given
        complex_obj_one = FakeComplexType(fake_field=123)
        fake_datapoint = FakeDatapointOne(complex_obj_one)
        # when / then
        with pytest.raises(DataPointCannotBeOverriddenError):
            context.add(fake_datapoint, fake_datapoint)

    def test_get_should_raise_if_no_datapoint_exists(
        self, context: InMemoryDataPointContext[FakeParams]
    ) -> None:
        # given / when / then
        with pytest.raises(DataPointIsNotProducedError):
            context.get(FakeDatapointOne)
