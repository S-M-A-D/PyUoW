import typing as t


class BatchError(Exception):
    pass


class CannotAddExistingEntityError(BatchError):
    pass


class CannotUpdateNewEntityError(BatchError):
    pass


class CannotDeleteNewEntityError(BatchError):
    pass


class BatchShutError(BatchError):
    pass


class DuplicateEntityInBatchError(BatchError):
    def __init__(
        self,
        entity_class: str,
        entity_id: t.Any,
        prior_op: str,
    ) -> None:
        super().__init__(
            f"{entity_class}[{entity_id}] has already been added to batch"
            f" with {prior_op} operation"
        )
        self.entity_class = entity_class
        self.entity_id = entity_id
        self.prior_op = prior_op
