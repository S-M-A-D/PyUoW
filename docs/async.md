# Async support

PyUoW is sync-first but provides an async twin for every module where async matters. The convention is uniform: an `aio/` sub-package sits next to the sync version, exporting the same names with `async def` signatures.

## Module map

| Sync                                  | Async                                          |
| ------------------------------------- | ---------------------------------------------- |
| `pyuow.unit`                          | `pyuow.unit.aio`                               |
| `pyuow`                               | `pyuow.aio` (re-exports the async unit API)    |
| `pyuow.work`                          | `pyuow.work.aio`                               |
| `pyuow.work.noop`                     | `pyuow.work.aio.noop`                          |
| `pyuow.work.transactional`            | `pyuow.work.aio.transactional`                 |
| `pyuow.work.transactional.domain`     | `pyuow.work.aio.transactional.domain`          |
| `pyuow.repository`                    | `pyuow.repository.aio`                         |
| `pyuow.repository.domain`             | `pyuow.repository.aio.domain`                  |
| `pyuow.datapoint`                     | `pyuow.datapoint.aio`                          |
| `pyuow.context.datapoint`             | `pyuow.context.datapoint.aio`                  |
| `pyuow.context.datapoint.in_memory`   | `pyuow.context.datapoint.aio.in_memory`        |
| `pyuow.domain.event`                  | `pyuow.domain.aio.event`                       |
| `pyuow.contrib.sqlalchemy.work`       | `pyuow.contrib.sqlalchemy.aio.work`            |
| `pyuow.contrib.sqlalchemy.repository` | `pyuow.contrib.sqlalchemy.aio.repository`      |

## What does *not* have an async version

A number of modules are pure data — no I/O, nothing to await:

- `pyuow.result` (`Result`)
- `pyuow.context` (`BaseContext`, `BaseParams`)
- `pyuow.entity` (`Entity`, `AuditedEntity`, `Version`, ...)
- `pyuow.domain.base` (`Model`, `Batch`, `Change`, `ChangeType`)
- `pyuow.clock`, `pyuow.types`

You use these from both sync and async code unchanged.

## Picking an entry point

For a typical async app, your imports look like:

```python
from pyuow.aio import (
    ConditionalUnit,
    ErrorUnit,
    FinalUnit,
    RunUnit,
)
from pyuow import BaseContext, BaseParams, Result   # sync-agnostic
from pyuow.work.aio.noop import NoOpWorkManager     # async manager
```

The `pyuow.aio` package is a convenience namespace — it re-exports the unit primitives from `pyuow.unit.aio` at the top level.

## Sync ↔ async cannot be mixed mid-flow

A `ConditionalUnit` from `pyuow.aio` cannot chain into a `RunUnit` from `pyuow` and vice versa. The signatures don't match (`__call__` is `async def` in one, regular `def` in the other) and `>>` returns the wrong shape.

Pick one model per flow. If you need to call sync code from an async unit, wrap it with `asyncio.to_thread(...)` or similar — that's an application concern, not a PyUoW concern.

## Examples side-by-side

See the [Quickstart](quickstart.md) for a sync example and the [Datapoints](concepts/datapoints.md#async-variant) page for the async equivalent.
