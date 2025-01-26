import typing as t
from abc import ABC, abstractmethod

from .base import ModelEvent


class DomainEventPublisher(ABC):
    @abstractmethod
    def __call__(self, events: t.Sequence[ModelEvent[t.Any]]) -> None:
        pass
