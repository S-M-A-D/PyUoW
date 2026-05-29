import datetime
import time


def offset_naive_utcnow() -> datetime.datetime:
    return datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)


def nano_timestamp_utc() -> int:
    return time.time_ns()
