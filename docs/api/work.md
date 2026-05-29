# `pyuow.work`

Work Manager protocols and built-in implementations.

::: pyuow.work.base
    options:
      members:
        - BaseWorkManager
        - BaseUnitProxy

## `pyuow.work.noop`

::: pyuow.work.noop.impl
    options:
      members:
        - NoOpWorkManager
        - NoOpUnitProxy

## `pyuow.work.transactional`

::: pyuow.work.transactional.base
    options:
      members:
        - BaseTransaction
        - BaseTransactionManager

::: pyuow.work.transactional.impl
    options:
      members:
        - TransactionalWorkManager
        - TransactionalUnitProxy

## `pyuow.work.transactional.domain`

::: pyuow.work.transactional.domain.impl
    options:
      members:
        - DomainTransactionalWorkManager
        - DomainUnit

## `pyuow.work.aio`

::: pyuow.work.aio.base
    options:
      members:
        - BaseWorkManager
        - BaseUnitProxy

::: pyuow.work.aio.noop.impl
    options:
      members:
        - NoOpWorkManager

::: pyuow.work.aio.transactional.impl
    options:
      members:
        - TransactionalWorkManager

::: pyuow.work.aio.transactional.domain.impl
    options:
      members:
        - DomainTransactionalWorkManager
