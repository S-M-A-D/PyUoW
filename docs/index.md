# PyUoW

> **Unit of Work pattern for Python — composable units, transactional work managers, and a domain model toolkit.**

PyUoW helps you structure business logic as a chain of small, testable units. Each unit does one thing; units compose into flows; flows run inside a **Work Manager** that handles transactions, batching, and domain events for you.

---

## Why PyUoW?

- **Composable** — write each step as a unit, chain them with the `>>` operator, run the result inside a manager.
- **Async-first** — every primitive ships with a sync and an async (`.aio`) version. Pick one, mix freely.
- **Domain-aware** — entities, audited entities, soft-deletion, versioning, and an event-emitting `Model` base are first-class.
- **Storage-agnostic** — repositories are abstract; a SQLAlchemy integration ships under `pyuow.contrib.sqlalchemy`.
- **Strictly typed** — the entire surface passes `mypy --strict`.

---

## At a glance

```python
from dataclasses import dataclass

from pyuow import (
    BaseContext,
    BaseParams,
    ConditionalUnit,
    ErrorUnit,
    FinalUnit,
    Result,
    RunUnit,
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


work = NoOpWorkManager()
result = work.by(flow).do_with(Ctx(params=Greeting(name="Alice")))
assert result.get() == "greeted"
```

---

## How the pieces fit together

```text
            ┌──────────────────────────────────┐
            │             Context              │
            │  (carries params + flow state)   │
            └──────────────────────────────────┘
                            │
                            ▼
   ┌─────────────────────────────────────────────────────────┐
   │                       Flow                              │
   │                                                         │
   │  Conditional  ─►  Run  ─►  Run  ─►  Final  ──►  Result  │
   │       │                                                 │
   │       └── on_failure ─►  Error/Final                    │
   └─────────────────────────────────────────────────────────┘
                            │
                            ▼
            ┌──────────────────────────────────┐
            │           Work Manager           │
            │   (transaction, batch, events)   │
            └──────────────────────────────────┘
```

---

## Next steps

- [Install PyUoW](installation.md)
- [Run the Quickstart](quickstart.md)
- Learn the [concepts](concepts/units.md)
- Browse the [API reference](api/pyuow.md)
