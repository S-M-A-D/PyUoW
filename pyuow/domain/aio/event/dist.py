import typing as t
from abc import ABC, abstractmethod

from ...base import ModelEvent


class EventHandler(ABC):
    @abstractmethod
    async def __call__(self, events: t.Sequence[ModelEvent[t.Any]]) -> None:
        raise NotImplementedError
