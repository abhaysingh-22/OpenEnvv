"""Base task class for OpenEnv."""
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from env.models import Observation, Action


class BaseTask(ABC):
    """Abstract base class for all tasks."""
    
    def __init__(self, task_id: str, title: str, description: str):
        """
        Initialize the base task.
        
        Args:
            task_id: Unique identifier for the task
            title: Task title
            description: Task description
        """
        self.task_id = task_id
        self.title = title
        self.description = description
        self.state: Optional[Observation] = None
        self.completed = False
    
    @abstractmethod
    def reset(self) -> Observation:
        """Reset the task to initial state."""
        pass
    
    @abstractmethod
    def step(self, action: Action) -> Observation:
        """
        Execute one step of the task.
        
        Args:
            action: The action to execute
            
        Returns:
            Updated state (Observation)
        """
        pass
    
    @abstractmethod
    def is_complete(self) -> bool:
        """Check if the task has been completed successfully."""
        pass
