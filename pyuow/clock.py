import datetime


def offset_naive_utcnow() -> datetime.datetime:
    return datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)


def nano_timestamp_utc() -> int:
    return int(offset_naive_utcnow().timestamp() * 1e9)
