# `pyuow.domain`

The `Model` + `Batch` toolkit, the exception tree, and domain events.

::: pyuow.domain
    options:
      members:
        - Model
        - Batch
        - Change
        - ChangeType
        - BatchError
        - BatchShutError
        - CannotAddExistingEntityError
        - CannotUpdateNewEntityError
        - CannotDeleteNewEntityError
        - DuplicateEntityInBatchError

## `pyuow.domain.event`

::: pyuow.domain.event
    options:
      members:
        - ModelEvent
        - ModelCreatedEvent
        - ModelDeletedEvent
        - EventHandler

## `pyuow.domain.aio.event`

::: pyuow.domain.aio.event
    options:
      members:
        - EventHandler
