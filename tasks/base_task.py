"""Base task class for OpenEnv."""
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


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
        self.state = None
        self.completed = False
    
    @abstractmethod
    def reset(self) -> Dict[str, Any]:
        """Reset the task to initial state."""
        pass
    
    @abstractmethod
    def step(self, action: str) -> Dict[str, Any]:
        """
        Execute one step of the task.
        
        Args:
            action: The action to execute
            
        Returns:
            Updated state
        """
        pass
    
    @abstractmethod
    def is_complete(self) -> bool:
        """Check if the task has been completed successfully."""
        pass
    
    def get_state(self) -> Dict[str, Any]:
        """Get the current task state."""
        return self.state
