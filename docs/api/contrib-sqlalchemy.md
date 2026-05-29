# `pyuow.contrib.sqlalchemy`

SQLAlchemy 2.x integration. Requires the `sqlalchemy` extra:

```bash
pip install "pyuow[sqlalchemy]"
```

## Tables

::: pyuow.contrib.sqlalchemy.tables
    options:
      members:
        - BaseTable
        - EntityTable
        - AuditedEntityTable
        - SoftDeletableEntityTable
        - VersionedEntityTable

## Sync work

::: pyuow.contrib.sqlalchemy.work
    options:
      members:
        - SqlAlchemyTransaction
        - SqlAlchemyTransactionManager
        - SqlAlchemyReadOnlyTransactionManager

## Sync repository

::: pyuow.contrib.sqlalchemy.repository
    options:
      members:
        - BaseSqlAlchemyEntityRepository
        - BaseSqlAlchemyRepositoryFactory

## Async work

::: pyuow.contrib.sqlalchemy.aio.work
    options:
      members:
        - SqlAlchemyTransaction
        - SqlAlchemyTransactionManager
        - SqlAlchemyReadOnlyTransactionManager

## Async repository

::: pyuow.contrib.sqlalchemy.aio.repository
    options:
      members:
        - BaseSqlAlchemyEntityRepository
        - BaseSqlAlchemyRepositoryFactory
