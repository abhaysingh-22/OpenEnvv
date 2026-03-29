"""Abstract base class for all tasks."""
from abc import ABC, abstractmethod
from typing import Optional
from env.models import Observation, Action


class BaseTask(ABC):
    """Every task must implement reset(), step(), and is_complete()."""

    def __init__(self, task_id: str, title: str, description: str):
        self.task_id = task_id
        self.title = title
        self.description = description
        self.state: Optional[Observation] = None
        self.completed = False

    @abstractmethod
    def reset(self) -> Observation:
        """Reset to initial state."""
        pass

    @abstractmethod
    def step(self, action: Action) -> Observation:
        """Execute one action and return the updated observation."""
        pass

    @abstractmethod
    def is_complete(self) -> bool:
        """Whether the task has been completed successfully."""
        pass
