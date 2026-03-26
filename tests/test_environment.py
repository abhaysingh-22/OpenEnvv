"""Tests for the environment module."""
import pytest
from env import Environment
from tasks import EasyTask
from graders import SupportGrader


def test_environment_initialization(sample_task, sample_grader):
    """Test environment initialization."""
    env = Environment(sample_task, sample_grader, max_steps=100)
    assert env.max_steps == 100
    assert env.current_step == 0
    assert env.done == False


def test_environment_reset(sample_task, sample_grader):
    """Test environment reset."""
    env = Environment(sample_task, sample_grader)
    state = env.reset()
    assert state is not None
    assert env.current_step == 0
    assert env.done == False


def test_environment_step(sample_task, sample_grader):
    """Test environment step."""
    env = Environment(sample_task, sample_grader)
    env.reset()
    observation, reward, done, info = env.step("test_action")
    assert observation is not None
    assert isinstance(reward, float)
    assert isinstance(done, bool)
    assert isinstance(info, dict)
