"""Tests for the rewards module."""
import pytest
from graders.rewards import RewardCalculator


def test_reward_calculator_initialization():
    """Test reward calculator initialization."""
    calc = RewardCalculator(max_reward=1.0, step_penalty=0.01)
    assert calc.max_reward == 1.0
    assert calc.step_penalty == 0.01


def test_completion_reward():
    """Test completion reward calculation."""
    calc = RewardCalculator()
    reward = calc.calculate_completion_reward(steps_taken=10, max_steps=100)
    assert isinstance(reward, float)
    assert 0 <= reward <= 1.0


def test_partial_reward():
    """Test partial reward calculation."""
    calc = RewardCalculator()
    reward = calc.calculate_partial_reward(progress=0.5)
    assert reward == 0.5


def test_penalty_calculation():
    """Test penalty calculation."""
    calc = RewardCalculator()
    penalty = calc.calculate_penalty('invalid_action')
    assert penalty == 0.1
