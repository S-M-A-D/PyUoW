from datetime import datetime

from pyuow.clock import offset_naive_utcnow


def test_offset_naive_utcnow_should_produce_offset_naive_utc_datetime() -> (
    None
):
    # when
    result = offset_naive_utcnow()
    # then
    assert isinstance(result, datetime)
    assert result.tzinfo is None
