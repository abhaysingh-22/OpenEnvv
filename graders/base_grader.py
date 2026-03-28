"""Base grader class for OpenEnv."""
from abc import ABC, abstractmethod
from typing import Any, Dict
from env.models import State, Action, Reward


class BaseGrader(ABC):
    """Abstract base class for all graders."""
    
    def __init__(self):
        """Initialize the base grader."""
        self.scores = []
    
    @abstractmethod
    def grade(self, state: State, action: Action, is_complete: bool) -> Reward:
        """
        Grade the current state.
        
        Args:
            state: Current environment state
            action: The action enacted
            is_complete: Whether the task is complete
            
        Returns:
            Reward object
        """
        pass
    
    def get_score_history(self) -> list:
        """Get the history of scores."""
        return self.scores
    
    def reset_scores(self) -> None:
        """Reset the score history."""
        self.scores = []
