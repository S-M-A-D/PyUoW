# pyuow API Reference

Complete public export list organized by namespace. Items marked **(async)** belong to the parallel async namespace under `.aio`.

## `pyuow` (top-level)

Re-exports from sub-packages. Use these for sync code.

| Name | Source |
|---|---|
| `AttributeCannotBeOverriddenError` | `pyuow.context.exceptions` |
| `BaseContext` | `pyuow.context.base` |
| `BaseImmutableContext` | `pyuow.context.base` |
| `BaseMutableContext` | `pyuow.context.base` |
| `BaseParams` | `pyuow.context.base` |
| `BaseUnit` | `pyuow.unit.base` |
| `CannotReassignUnitError` | `pyuow.unit.exceptions` |
| `ConditionalUnit` | `pyuow.unit.impl` |
| `ErrorUnit` | `pyuow.unit.impl` |
| `FinalUnit` | `pyuow.unit.impl` |
| `FinalUnitError` | `pyuow.unit.exceptions` |
| `FlowUnit` | `pyuow.unit.impl` |
| `MissingOutError` | `pyuow.result.exceptions` |
| `Result` | `pyuow.result.impl` |
| `RunUnit` | `pyuow.unit.impl` |

## `pyuow.aio`

Async equivalents of the unit classes only. Context, params, and `Result` come from the top-level `pyuow`.

`BaseUnit`, `ConditionalUnit`, `ErrorUnit`, `FinalUnit`, `FlowUnit`, `RunUnit`

## `pyuow.context`

| Name | Notes |
|---|---|
| `BaseContext` | Generic over `PARAMS` |
| `BaseImmutableContext` | Frozen variant |
| `BaseMutableContext` | Write-once-per-attribute |
| `BaseParams` | Marker base for params dataclasses |
| `AttributeCannotBeOverriddenError` | Raised on attribute reassignment |

## `pyuow.context.domain`

| Name | Notes |
|---|---|
| `BaseDomainContext` | `BaseContext` subclass that adds `batch: Batch` |

## `pyuow.context.datapoint` / `pyuow.context.datapoint.aio`

`BaseDataPointConsumerContext`, `BaseDataPointContext`, `BaseDataPointProducerContext`

## `pyuow.context.datapoint.in_memory` / `pyuow.context.datapoint.aio.in_memory`

`InMemoryDataPointContext`

## `pyuow.datapoint` / `pyuow.datapoint.aio`

| Name | Notes |
|---|---|
| `BaseDataPointContainer` | sync only |
| `BaseDataPointsDict` | sync only |
| `BaseDataPointSpec` | sync only |
| `BaseDataPointConsumer` | sync + async |
| `BaseDataPointProducer` | sync + async |
| `ConsumesDataPoints` | sync + async |
| `ProducesDataPoints` | sync + async |
| `DataPointCannotBeOverriddenError` | sync only |
| `DataPointIsNotProducedError` | sync only |

## `pyuow.domain`

| Name | Notes |
|---|---|
| `Batch` | Aggregate of pending entity changes |
| `Change` | Single pending change (add/update/delete) |
| `ChangeType` | Enum for change kinds |
| `Model` | Abstract base for aggregate roots |
| `BatchError`, `BatchShutError` | Exceptions |
| `CannotAddExistingEntityError` | Exception |
| `CannotDeleteNewEntityError` | Exception |
| `CannotUpdateNewEntityError` | Exception |
| `DuplicateEntityInBatchError` | Exception |

## `pyuow.domain.event` / `pyuow.domain.aio.event`

| Name | Notes |
|---|---|
| `EventHandler` | sync + async |
| `ModelEvent` | sync only |
| `ModelCreatedEvent` | sync only |
| `ModelDeletedEvent` | sync only |

## `pyuow.entity`

| Name | Notes |
|---|---|
| `Entity` | Base entity, generic over id type |
| `AuditedEntity` | Adds `created_at`, `updated_at` |
| `SoftDeletableEntity` | Adds `deleted_at` |
| `Version` | Optimistic-locking version wrapper |
| `VersionedEntity` | Adds `version: Version` |

## `pyuow.repository` / `pyuow.repository.aio`

| Name | Notes |
|---|---|
| `BaseEntityRepository` | Abstract — combines read + write |
| `BaseReadOnlyEntityRepository` | Abstract — read methods only |
| `BaseWriteOnlyEntityRepository` | Abstract — write methods only |
| `BaseRepositoryFactory` | Looks up repositories by entity type via `repo_for(EntityType)` |
| `DomainRepository` | Processes `Batch` instances |

## `pyuow.result`

| Name | Notes |
|---|---|
| `Result[OUT]` | Construct via `Result.ok(value)`, `Result.error(exc)`, `Result.empty()` |
| `MissingOutError` | Raised by `Result.get()` on empty/error results |

Key methods: `get()`, `is_ok()`, `is_empty()`, `is_error()`, `map(fn)`, `and_then(fn)`, `unwrap_or(default)`.

## `pyuow.unit` / `pyuow.unit.aio`

| Name | Notes |
|---|---|
| `BaseUnit[CONTEXT, OUT]` | Abstract — `__call__(ctx) -> Result[OUT]` |
| `RunUnit` | Override `run(ctx) -> None` for side-effecting steps |
| `ConditionalUnit` | Override `condition(ctx) -> bool`; takes `on_failure` parameter |
| `FinalUnit` | Override `finish(ctx) -> Result[OUT]`; terminates the flow |
| `ErrorUnit` | Takes `exc: Exception`; produces `Result.error(exc)` |
| `FlowUnit` | The built flow returned by `.build()` |
| `CannotReassignUnitError` | Raised when reusing a unit instance |
| `FinalUnitError` | Raised when chaining after `FinalUnit` |
| `FlowNotTerminatedError` | Raised when `.build()` finds no terminal unit |

## `pyuow.work` / `pyuow.work.aio`

| Name | Notes |
|---|---|
| `BaseUnitProxy[CONTEXT, OUT]` | Proxy returned by `WorkManager.by(unit)` |
| `BaseWorkManager` | Abstract — `by(unit) -> BaseUnitProxy` |

### `pyuow.work.noop` / `pyuow.work.aio.noop`

`NoOpWorkManager`, `NoOpUnitProxy` — passes unit execution through unchanged.

### `pyuow.work.transactional` / `pyuow.work.aio.transactional`

| Name | Notes |
|---|---|
| `BaseTransaction` | Abstract |
| `BaseTransactionManager` | Abstract — `transaction() -> ContextManager[BaseTransaction]` |
| `TransactionalUnitProxy` | Wraps a unit in commit/rollback |
| `TransactionalWorkManager` | Constructed with a `transaction_manager` |

### `pyuow.work.transactional.domain` / `pyuow.work.aio.transactional.domain`

| Name | Notes |
|---|---|
| `DomainUnit` | Unit that operates on a domain context |
| `DomainTransactionalWorkManager` | Calls a `batch_handler(batch)` after the unit if context is a `BaseDomainContext` |

## `pyuow.contrib.sqlalchemy` / `pyuow.contrib.sqlalchemy.aio`

Requires `pip install "pyuow[sqlalchemy]"`.

| Name | Notes |
|---|---|
| `SqlAlchemyTransactionManager` | Wraps a SQLAlchemy `Engine` / `AsyncEngine`; supports nested transactions |
| `SqlAlchemyReadOnlyTransactionManager` | Autocommit read variant |
| `SqlAlchemyTransaction` | The transaction type yielded by the manager; exposes `.it()` for the session |
| `BaseSqlAlchemyEntityRepository` | Abstract — implement `to_entity` and `to_record` |
| `BaseSqlAlchemyRepositoryFactory` | Wires entity types to repository instances |

Sync-only re-exports (also under `pyuow.contrib.sqlalchemy`):

`AuditedEntityTable`, `BaseTable`, `EntityTable`, `SoftDeletableEntityTable`, `VersionedEntityTable`

The async namespace omits the table mixins (they're SQLAlchemy declarative types and work the same in both).

## Key signatures cheat sheet

```python
# Result
Result.ok(value: OUT) -> Result[OUT]
Result.error(exc: Exception) -> Result[OUT]
Result.empty() -> Result[OUT]
result.get() -> OUT                   # raises if empty/error
result.is_ok() -> bool
result.is_empty() -> bool
result.is_error() -> bool
result.map(fn: Callable[[OUT], NEW]) -> Result[NEW]
result.and_then(fn: Callable[[OUT], Result[NEW]]) -> Result[NEW]
result.unwrap_or(default: OUT) -> OUT

# Flow construction
flow = (UnitA() >> UnitB() >> FinalUnit()).build()    # returns FlowUnit

# Work manager execution
result = manager.by(flow).do_with(context)            # sync: Result[OUT]
result = await manager.by(flow).do_with(context)      # async: Result[OUT]

# SQLAlchemy transaction usage
with sqla_manager.transaction() as trx:
    session = trx.it()
    # ... use session ...
```
