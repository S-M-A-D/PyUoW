import pytest

from pyuow.datapoint import BaseDataPointSpec


class TestBaseDataPointSpec:
    def test_should_raise_if_ref_type_is_not_matching_value_type(self) -> None:
        # given
        FakeDatapoint = BaseDataPointSpec("fake_datapoint", int)
        # when / then
        with pytest.raises(TypeError):
            FakeDatapoint(1.0)  # type: ignore[arg-type]
