"""Dummy agent for baseline testing."""
from typing import Any, Dict
from .base_agent import BaseAgent


class DummyAgent(BaseAgent):
    """A simple dummy agent for baseline testing."""
    
    def __init__(self, agent_id: str = "dummy_0"):
        """Initialize the dummy agent."""
        super().__init__(agent_id, "DummyAgent")
    
    def act(self, observation: Dict[str, Any]) -> str:
        """
        Generate a dummy action.
        
        Args:
            observation: Current environment observation
            
        Returns:
            A simple predefined action
        """
        action = "dummy_action"
        self.action_history.append(action)
        return action
