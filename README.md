<p align="center">
  <a href="https://github.com/S-M-A-D/PyUoW">
    <img src="https://raw.githubusercontent.com/S-M-A-D/PyUoW/main/static/logo.png" alt="pyUoW" width="500">
  </a>
</p>

<p align="center">
  <em>Unit of Work for Python — composable units, transactional work managers, and a domain model toolkit.</em>
</p>

<p align="center">
  <a href="https://s-m-a-d.github.io/PyUoW/"><strong>📖 Read the docs</strong></a>
  &nbsp;·&nbsp;
  <a href="https://s-m-a-d.github.io/PyUoW/quickstart/">Quickstart</a>
  &nbsp;·&nbsp;
  <a href="https://pypi.org/project/pyuow/">PyPI</a>
</p>

<p align="center">
  <a href="https://pepy.tech/project/pyuow"><img src="https://static.pepy.tech/badge/pyuow" alt="Downloads"></a>
  <a href="https://github.com/S-M-A-D/PyUoW/actions/workflows/build.yaml"><img src="https://github.com/S-M-A-D/PyUoW/actions/workflows/build.yaml/badge.svg" alt="Build"></a>
  <a href="https://codecov.io/gh/S-M-A-D/PyUoW"><img src="https://codecov.io/gh/S-M-A-D/PyUoW/graph/badge.svg?token=L1Y13VT30W" alt="Codecov"></a>
  <img src="https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json" alt="Ruff">
  <img src="https://img.shields.io/pypi/pyversions/pyuow" alt="Python versions">
  <img src="https://img.shields.io/pypi/l/pyuow" alt="License">
</p>

---

## What is PyUoW?

PyUoW is a Python implementation of the [Unit of Work](https://martinfowler.com/eaaCatalog/unitOfWork.html) behavioural pattern. It gives you small, typed building blocks for business logic that compose into a **flow** and run inside a **Work Manager** that handles transactions, batching, and domain events.

The result: business logic that reads top-to-bottom, separates orchestration from execution, and stays testable as it grows.

### Highlights

- **Composable units** — write each step as a `ConditionalUnit` / `RunUnit` / `FinalUnit`, chain them with `>>`, validate the chain at build time.
- **Transactional out of the box** — a SQLAlchemy adapter ships in `pyuow.contrib.sqlalchemy` (sync + async), with nested-transaction support.
- **Domain-first** — `Entity`, `AuditedEntity`, `SoftDeletableEntity`, `VersionedEntity`, and an event-emitting `Model` base, all immutable dataclasses.
- **Sync and async parity** — every primitive has an `aio/` twin; pick one per flow.
- **Strict types** — passes `mypy --strict`; runs on Python 3.10 through 3.14.

---

## Install

```bash
pip install pyuow                # core
pip install "pyuow[sqlalchemy]"  # with SQLAlchemy integration
```

Python ≥ 3.10.

## At a glance

```python
from dataclasses import dataclass

from pyuow import (
    BaseContext, BaseParams, ConditionalUnit, ErrorUnit,
    FinalUnit, Result, RunUnit,
)
from pyuow.work.noop import NoOpWorkManager


@dataclass(frozen=True)
class Greeting(BaseParams):
    name: str


@dataclass
class Ctx(BaseContext[Greeting]):
    params: Greeting


class IsNamePresent(ConditionalUnit[Ctx, str]):
    def condition(self, ctx: Ctx) -> bool:
        return bool(ctx.params.name)


class Greet(RunUnit[Ctx, str]):
    def run(self, ctx: Ctx) -> None:
        print(f"Hello, {ctx.params.name}!")


class Done(FinalUnit[Ctx, str]):
    def finish(self, ctx: Ctx) -> Result[str]:
        return Result.ok("greeted")


flow = (
    IsNamePresent(on_failure=ErrorUnit(exc=ValueError("name required")))
    >> Greet()
    >> Done()
).build()

result = NoOpWorkManager().by(flow).do_with(Ctx(params=Greeting(name="Alice")))
assert result.get() == "greeted"
```

## What's in the box

| Concept                                                                       | What it gives you                                                            |
| ----------------------------------------------------------------------------- | ---------------------------------------------------------------------------- |
| [Units & Flow](https://s-m-a-d.github.io/PyUoW/concepts/units/)               | `ConditionalUnit` / `RunUnit` / `FinalUnit` / `ErrorUnit`, chained with `>>` |
| [Result](https://s-m-a-d.github.io/PyUoW/concepts/result/)                    | `ok` / `error` / `empty` plus `.map`, `.and_then`, `.unwrap_or`              |
| [Context](https://s-m-a-d.github.io/PyUoW/concepts/context/)                  | Mutable, immutable, and domain-aware context bases                           |
| [Work Manager](https://s-m-a-d.github.io/PyUoW/concepts/work/)                | NoOp, transactional, and domain-transactional managers                       |
| [Domain Model](https://s-m-a-d.github.io/PyUoW/concepts/domain/)              | `Entity`, `AuditedEntity`, `Model`, `Batch`, events, typed exceptions        |
| [DataPoints](https://s-m-a-d.github.io/PyUoW/concepts/datapoints/)            | Typed producer / consumer contracts between units                            |
| [SQLAlchemy](https://s-m-a-d.github.io/PyUoW/integrations/sqlalchemy/)        | Ready-made repositories, table mixins, and transaction manager               |
| [Async](https://s-m-a-d.github.io/PyUoW/async/)                               | A sync and an `aio/` twin for every primitive                                |

## Contributing

PRs welcome — see [CONTRIBUTING.md](CONTRIBUTING.md) for the dev setup, or run:

```bash
poetry install --with docs
make tests        # pytest + coverage
make fmt          # ruff + mypy
make docs-serve   # live preview at http://127.0.0.1:8000
```
