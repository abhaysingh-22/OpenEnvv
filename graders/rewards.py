"""Reward accumulator — tracks total reward and produces normalized scores."""


class RewardCalculator:
    """
    Accumulates step rewards and normalizes to [0, 1].

    Reward scale:
        correct action  +0.4 to +0.9
        wrong action    -0.5
        repeated action -0.3
        extra step      -0.1 each
    """

    def __init__(self):
        self.total_reward = 0.0
        self.last_action = None

    def add_reward(self, amount: float) -> None:
        self.total_reward += amount

    def get_score(self, max_reward: float = 0.9) -> float:
        score = self.total_reward / max_reward if max_reward > 0 else 0.0
        return max(0.0, min(1.0, score))

    def reset(self) -> None:
        self.total_reward = 0.0
        self.last_action = None
