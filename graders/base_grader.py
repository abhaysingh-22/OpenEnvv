"""Abstract base class for all graders."""
from abc import ABC, abstractmethod
from env.models import State, Action, Reward


class BaseGrader(ABC):
    """Graders evaluate agent actions and produce Reward objects."""

    def __init__(self):
        self.scores = []

    @abstractmethod
    def grade(self, state: State, action: Action, is_complete: bool) -> Reward:
        """Score the action taken in the given state."""
        pass

    def get_score_history(self) -> list:
        return self.scores

    def reset_scores(self) -> None:
        self.scores = []
