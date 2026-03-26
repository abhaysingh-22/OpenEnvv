"""Base grader class for OpenEnv."""
from abc import ABC, abstractmethod
from typing import Any, Dict


class BaseGrader(ABC):
    """Abstract base class for all graders."""
    
    def __init__(self):
        """Initialize the base grader."""
        self.scores = []
    
    @abstractmethod
    def grade(self, state: Dict[str, Any], is_complete: bool) -> float:
        """
        Grade the current state.
        
        Args:
            state: Current environment state
            is_complete: Whether the task is complete
            
        Returns:
            Reward score
        """
        pass
    
    def get_score_history(self) -> list:
        """Get the history of scores."""
        return self.scores
    
    def reset_scores(self) -> None:
        """Reset the score history."""
        self.scores = []
