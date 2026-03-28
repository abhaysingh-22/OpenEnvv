"""SIMPLIFIED Reward calculation for OpenEnv.

Only tracks:
- Correct action: +0.4
- Correct response: +0.3
- Good tone: +0.2
- Efficiency penalty: -0.1 per extra step
- Wrong action: -0.5
- Repeated action: -0.3
"""


class RewardCalculator:
    """
    Simplified reward calculator with deterministic scoring.
    
    Components:
    - correct_action: +0.4
    - correct_response: +0.3
    - good_tone: +0.2
    - efficiency: -0.1 per extra step (beyond minimum)
    - wrong_action: -0.5
    - repeated_action: -0.3
    
    Final score = clamp(total_reward / MAX_REWARD, 0, 1)
    """
    
    def __init__(self):
        """Initialize with simple tracking."""
        self.total_reward = 0.0
        self.last_action = None
    
    def add_reward(self, amount: float) -> None:
        """Add to total reward."""
        self.total_reward += amount
    
    def get_score(self, max_reward: float = 0.9) -> float:
        """Get normalized final score (0 to 1)."""
        score = self.total_reward / max_reward if max_reward > 0 else 0.0
        return max(0.0, min(1.0, score))
    
    def reset(self) -> None:
        """Reset for new episode."""
        self.total_reward = 0.0
        self.last_action = None
