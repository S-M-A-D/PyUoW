from datetime import datetime

from pyuow.clock import nano_timestamp_utc, offset_naive_utcnow


def test_offset_naive_utcnow_should_produce_offset_naive_utc_datetime() -> (
    None
):
    # when
    result = offset_naive_utcnow()
    # then
    assert isinstance(result, datetime)
    assert result.tzinfo is None


def test_nano_timestamp_utc_should_produce_19digits_timestamp() -> None:
    # when
    timestamp = nano_timestamp_utc()
    # then
    assert isinstance(timestamp, int)
    assert len(str(timestamp)) == 19
