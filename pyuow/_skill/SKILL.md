---
name: pyuow
description: Use when writing Python code that uses the pyuow library — defining units of work, chaining flows with the >> operator, building work managers, integrating SQLAlchemy persistence, or handling FlowNotTerminatedError, FinalUnitError, CannotReassignUnitError, MissingOutError, or other pyuow.* exceptions.
---

# pyuow

## Mental model

**There is no class called `UnitOfWork`.** pyuow's core abstraction is `BaseUnit` — small composable steps. You chain units with `>>`, call `.build()`, and run the result through a `WorkManager`. Every run returns a `Result[T]`.

```
flow = (UnitA() >> UnitB() >> FinalUnit()).build()
result = WorkManager().by(flow).do_with(context)
```

## Canonical sync flow

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

## Sync vs async — pick ONE per flow

| Sync namespace | Async namespace |
|---|---|
| `pyuow` (top-level units) | `pyuow.aio` |
| `pyuow.work.noop` | `pyuow.work.aio.noop` |
| `pyuow.work.transactional` | `pyuow.work.aio.transactional` |
| `pyuow.work.transactional.domain` | `pyuow.work.aio.transactional.domain` |
| `pyuow.repository` | `pyuow.repository.aio` |
| `pyuow.contrib.sqlalchemy` | `pyuow.contrib.sqlalchemy.aio` |
| `pyuow.datapoint` | `pyuow.datapoint.aio` |

Never mix. Work managers expect units of matching async-ness. `BaseContext`, `BaseParams`, and `Result` are shared (not split).

## Three pillars

- **Units & flows** — `BaseUnit`, `RunUnit`, `ConditionalUnit`, `FinalUnit`, `ErrorUnit`. Chain with `>>`. Every flow must end in a `FinalUnit` or `ErrorUnit`. Call `.build()` once to produce a `FlowUnit`. Each unit instance belongs to one flow; create fresh instances for reuse.
- **Work managers** — `NoOpWorkManager` (no transaction), `TransactionalWorkManager` (wraps a `BaseTransactionManager` for commit/rollback), `DomainTransactionalWorkManager` (also calls a batch handler after the unit if the context inherits `BaseDomainContext`). Same shape: `manager.by(flow).do_with(ctx) -> Result[T]`.
- **Persistence (optional)** — `pyuow.contrib.sqlalchemy` is an opt-in extra. Install with `pip install "pyuow[sqlalchemy]"`. Exposes `SqlAlchemyTransactionManager`, `SqlAlchemyReadOnlyTransactionManager`, `BaseSqlAlchemyEntityRepository`, `BaseSqlAlchemyRepositoryFactory`, and table mixins (`EntityTable`, `AuditedEntityTable`, `SoftDeletableEntityTable`, `VersionedEntityTable`).

See `patterns.md` for full runnable recipes. See `api-reference.md` for the complete public export list.

## Common mistakes

| Symptom | Cause | Fix |
|---|---|---|
| `ImportError: cannot import name 'UnitOfWork'` | The class doesn't exist | Use `BaseUnit` subclasses + `>>` + `.build()` + a `WorkManager` |
| `ImportError: cannot import name 'Command'` | The class doesn't exist | Subclass `RunUnit`, `ConditionalUnit`, or `FinalUnit` |
| `ImportError: cannot import name 'AsyncUnitOfWork'` | Wrong namespace, wrong name | Import async unit classes from `pyuow.aio`, not `pyuow` |
| `ModuleNotFoundError: No module named 'pyuow.sqlalchemy'` | Wrong import path | It's `pyuow.contrib.sqlalchemy` (sync) or `pyuow.contrib.sqlalchemy.aio` (async) |
| Import works at runtime but immediately fails with "install pyuow[sqlalchemy]" | SQLAlchemy is an optional extra | `pip install "pyuow[sqlalchemy]"` |
| `FlowNotTerminatedError` on `.build()` | Chain has no `FinalUnit` or `ErrorUnit` at the end | End every flow with a `FinalUnit` or `ErrorUnit` |
| `FinalUnitError` when chaining | Chained another unit *after* a `FinalUnit` | `FinalUnit` is terminal — nothing follows it |
| `CannotReassignUnitError` | Reused a unit instance in two flows | Each unit instance belongs to one flow — create fresh instances |
| `MissingOutError` on `result.get()` | Called `.get()` on `Result.empty()` or `Result.error(...)` | Check `result.is_ok()` first, or use `result.unwrap_or(default)` |
| `AttributeCannotBeOverriddenError` on context assignment | Reassigned an existing attribute on a `BaseMutableContext` | Mutable contexts are write-once per attribute; use a different key |
| Repository lookup raises `KeyError` | Called `repo_for(EntityType)` for an unregistered entity | Register the entity-to-repository mapping in your `BaseRepositoryFactory` subclass |
| Mixed sync and async imports in same flow | Used `pyuow.unit.RunUnit` together with `pyuow.work.aio.*` | All units in a flow must come from matching sync or async namespace |

## Updating

If installed with `pyuow install-skill --project` (the default), this skill is a symlink to the installed pyuow package's `_skill/` directory and updates automatically with `pip install -U pyuow`. If symlinks aren't supported (Windows without Developer Mode), the installer falls back to a copy — re-run `pyuow install-skill --project --force` after upgrades to refresh it.
