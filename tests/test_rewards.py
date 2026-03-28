"""Tests for the rewards module."""
import pytest
from graders.rewards import RewardCalculator


def test_reward_calculator_initialization():
    """Test reward calculator initializes with zero reward."""
    calc = RewardCalculator()
    assert calc.total_reward == 0.0


def test_completion_reward():
    """Test adding completion rewards."""
    calc = RewardCalculator()
    calc.add_reward(0.9)
    assert calc.total_reward == 0.9


def test_partial_reward():
    """Test adding partial rewards."""
    calc = RewardCalculator()
    calc.add_reward(0.4)
    calc.add_reward(0.3)
    assert calc.total_reward == 0.7


def test_penalty_calculation():
    """Test penalty subtraction."""
    calc = RewardCalculator()
    calc.add_reward(0.9)
    calc.add_reward(-0.5)
    assert calc.total_reward == 0.4
