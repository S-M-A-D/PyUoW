# Installation

PyUoW is on PyPI and supports Python 3.9 through 3.14.

## Core install

```bash
pip install pyuow
```

## With SQLAlchemy integration

The SQLAlchemy adapter is shipped as an optional extra. Install both at once:

```bash
pip install "pyuow[sqlalchemy]"
```

This pulls in SQLAlchemy 2.x and unlocks the modules under `pyuow.contrib.sqlalchemy` (sync and async). See [SQLAlchemy integration](integrations/sqlalchemy.md) for usage.

## Using Poetry

```bash
poetry add pyuow
# or with the sqlalchemy extra
poetry add 'pyuow[sqlalchemy]'
```

## Using uv

```bash
uv add pyuow
# or
uv add 'pyuow[sqlalchemy]'
```

## Async support

There is **nothing extra to install** — every module that needs an async equivalent ships one under a sibling `aio/` package, for example:

| Sync                              | Async                                  |
| --------------------------------- | -------------------------------------- |
| `pyuow.unit`                      | `pyuow.unit.aio` (also `pyuow.aio`)    |
| `pyuow.work.transactional`        | `pyuow.work.aio.transactional`         |
| `pyuow.repository`                | `pyuow.repository.aio`                 |
| `pyuow.contrib.sqlalchemy.work`   | `pyuow.contrib.sqlalchemy.aio.work`    |
| `pyuow.contrib.sqlalchemy.repository` | `pyuow.contrib.sqlalchemy.aio.repository` |

See [Async support](async.md) for the conventions.

## Verifying the install

```python
import pyuow
print(pyuow.Result.ok(42))
# Result.ok(42)
```
