from dataclasses import dataclass

import pytest

from pyuow import DataPointCannotBeOverriddenError, DataPointIsNotProducedError
from pyuow.context import BaseParams
from pyuow.context.datapoint.aio.in_memory import InMemoryDataPointContext
from pyuow.datapoint import BaseDataPointName


@dataclass(frozen=True)
class FakeParams(BaseParams):
    pass


@dataclass(frozen=True)
class FakeComplexType:
    fake_field: int


FakeDatapointOne = BaseDataPointName[FakeComplexType]("fake_datapoint_one")
FakeDatapointTwo = BaseDataPointName[FakeComplexType]("fake_datapoint_two")


class TestInMemoryDataPointContext:
    @pytest.fixture
    def params(self) -> FakeParams:
        return FakeParams()

    @pytest.fixture
    def context(
        self, params: FakeParams
    ) -> InMemoryDataPointContext[FakeParams]:
        return InMemoryDataPointContext(params=params)

    async def test_async_should_properly_add_and_get_datapoints(
        self, context: InMemoryDataPointContext[FakeParams]
    ):
        # given
        complex_obj_one = FakeComplexType(fake_field=123)
        complex_obj_two = FakeComplexType(fake_field=456)
        fake_datapoint_one = FakeDatapointOne(complex_obj_one)
        fake_datapoint_two = FakeDatapointTwo(complex_obj_two)
        # when
        await context.add(fake_datapoint_one, fake_datapoint_two)
        # then
        datapoints = await context.get(FakeDatapointOne, FakeDatapointTwo)
        assert datapoints[FakeDatapointOne] == complex_obj_one
        assert datapoints[FakeDatapointTwo] == complex_obj_two

    async def test_async_add_should_raise_if_duplicated_datapoint_added(
        self, context: InMemoryDataPointContext[FakeParams]
    ):
        # given
        complex_obj_one = FakeComplexType(fake_field=123)
        fake_datapoint = FakeDatapointOne(complex_obj_one)
        # when / then
        with pytest.raises(DataPointCannotBeOverriddenError):
            await context.add(fake_datapoint, fake_datapoint)

    async def test_async_get_should_raise_if_no_datapoint_exists(
        self, context: InMemoryDataPointContext[FakeParams]
    ):
        # given / when / then
        with pytest.raises(DataPointIsNotProducedError):
            await context.get(FakeDatapointOne)
