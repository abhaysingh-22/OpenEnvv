"""Base agent class for OpenEnv."""
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class BaseAgent(ABC):
    """Abstract base class for all agents."""
    
    def __init__(self, agent_id: str, name: str):
        """
        Initialize the base agent.
        
        Args:
            agent_id: Unique identifier for the agent
            name: Agent name
        """
        self.agent_id = agent_id
        self.name = name
        self.action_history = []
    
    @abstractmethod
    def act(self, observation: Dict[str, Any]) -> str:
        """
        Generate an action based on observation.
        
        Args:
            observation: Current environment observation
            
        Returns:
            Action string
        """
        pass
    
    def reset(self) -> None:
        """Reset the agent state."""
        self.action_history = []
    
    def get_action_history(self) -> list:
        """Get the action history."""
        return self.action_history
