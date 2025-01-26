from unittest.mock import Mock

import pytest

from pyuow.datapoint import (
    BaseDataPointSpec,
    ConsumesDataPoints,
    DataPointIsNotProducedError,
    ProducesDataPoints,
)

FakeDatapoint = BaseDataPointSpec("fake_datapoint", int)
FakeExtraDatapoint = BaseDataPointSpec("fake_extra_datapoint", float)


class FakeObjThatProducesDataPoints(ProducesDataPoints):
    _produces = {FakeDatapoint}


class FakeObjThatConsumesDataPoints(ConsumesDataPoints):
    _consumes = {FakeDatapoint}


class TestConsumesDataPoints:
    def test_to_should_delegate_to_provider_proxy(self) -> None:
        # given
        fake_producer = Mock()
        obj_that_produces = FakeObjThatProducesDataPoints()
        # when
        proxy = obj_that_produces.to(fake_producer)
        # then
        assert isinstance(proxy, FakeObjThatProducesDataPoints.ProducerProxy)

    def test_to_add_should_delegate_datapoints_to_producer(self) -> None:
        # given
        fake_producer = Mock()
        obj_that_produces = FakeObjThatProducesDataPoints()
        datapoint = FakeDatapoint(1)
        # when
        obj_that_produces.to(fake_producer).add(datapoint)
        # then
        fake_producer.add.assert_called_once_with(datapoint)

    def test_to_add_should_raise_if_at_least_one_required_datapoint_is_missing(
        self,
    ) -> None:
        # given
        fake_producer = Mock()
        obj_that_produces = FakeObjThatProducesDataPoints()
        # when / then
        with pytest.raises(DataPointIsNotProducedError):
            obj_that_produces.to(fake_producer).add()

    def test_out_of_should_delegate_names_to_consumer(self) -> None:
        # given
        fake_consumer = Mock()
        datapoint = FakeDatapoint(1)
        fake_consumer.get.return_value = {FakeDatapoint: datapoint}
        obj_that_consumes = FakeObjThatConsumesDataPoints()
        # when
        obj_that_consumes.out_of(fake_consumer)
        # then
        fake_consumer.get.assert_called_once_with(FakeDatapoint)

    def test_out_of_should_raise_if_at_least_one_required_datapoint_is_missing(
        self,
    ) -> None:
        fake_consumer = Mock()
        datapoint = FakeExtraDatapoint(1.0)
        fake_consumer.get.return_value = {FakeExtraDatapoint: datapoint}
        obj_that_consumes = FakeObjThatConsumesDataPoints()
        # when / then
        with pytest.raises(
            DataPointIsNotProducedError,
            match=r"{BaseDataPointSpec\(name='[^']+', ref_type=<class '[^']+'>\)}",
        ):
            obj_that_consumes.out_of(fake_consumer)
