"""Reward calculation utilities."""
from typing import Dict, Any


class RewardCalculator:
    """Calculate rewards based on various metrics."""
    
    def __init__(self, max_reward: float = 1.0, step_penalty: float = 0.01):
        """
        Initialize reward calculator.
        
        Args:
            max_reward: Maximum possible reward
            step_penalty: Penalty per step taken
        """
        self.max_reward = max_reward
        self.step_penalty = step_penalty
    
    def calculate_completion_reward(self, steps_taken: int, max_steps: int) -> float:
        """
        Calculate reward for task completion.
        
        Args:
            steps_taken: Number of steps taken
            max_steps: Maximum allowed steps
            
        Returns:
            Reward value
        """
        penalty = steps_taken * self.step_penalty
        final_reward = self.max_reward - penalty
        return max(0, final_reward)
    
    def calculate_partial_reward(self, progress: float) -> float:
        """
        Calculate reward for partial task completion.
        
        Args:
            progress: Progress percentage (0-1)
            
        Returns:
            Reward value
        """
        return progress * self.max_reward
    
    def calculate_penalty(self, error_type: str) -> float:
        """
        Calculate penalty for errors.
        
        Args:
            error_type: Type of error
            
        Returns:
            Penalty value
        """
        penalties = {
            'invalid_action': 0.1,
            'policy_violation': 0.3,
            'forbidden_phrase': 0.2
        }
        return penalties.get(error_type, 0.0)
