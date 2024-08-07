from unittest.mock import AsyncMock, Mock

import pytest

from pyuow.datapoint import (
    BaseDataPointName,
    ConsumesDataPoints,
    DataPointIsNotProducedError,
    ProducesDataPoints,
)

FakeDatapoint = BaseDataPointName[int]("fake_datapoint")


class FakeObjThatProducesDataPoints(ProducesDataPoints):
    _produces = {FakeDatapoint}


class FakeObjThatConsumesDataPoints(ConsumesDataPoints):
    _consumes = {FakeDatapoint}


class TestConsumesDataPoints:
    def test_to_should_delegate_to_provider_proxy(self):
        # given
        fake_producer = Mock()
        obj_that_produces = FakeObjThatProducesDataPoints()
        # when
        proxy = obj_that_produces.to(fake_producer)
        # then
        assert isinstance(proxy, FakeObjThatProducesDataPoints.ProducerProxy)

    def test_to_add_should_delegate_datapoints_to_producer(self):
        # given
        fake_producer = AsyncMock()
        obj_that_produces = FakeObjThatProducesDataPoints()
        datapoint = FakeDatapoint(1)
        # when
        obj_that_produces.to(fake_producer).add(datapoint)
        # then
        fake_producer.add.assert_called_once_with(datapoint)

    def test_to_add_should_fail_if_at_least_one_required_datapoint_is_missing(
        self,
    ):
        # given
        fake_producer = AsyncMock()
        obj_that_produces = FakeObjThatProducesDataPoints()
        # when / then
        with pytest.raises(DataPointIsNotProducedError):
            obj_that_produces.to(fake_producer).add()

    def test_out_of_should_delegate_names_to_consumer(self):
        # given
        fake_consumer = AsyncMock()
        obj_that_consumes = FakeObjThatConsumesDataPoints()
        # when
        obj_that_consumes.out_of(fake_consumer)
        # then
        fake_consumer.get.assert_called_once_with(FakeDatapoint)
