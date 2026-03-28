"""Tests for the environment module."""
import pytest
from env.environment import Environment
from env.models import Action
from tasks.easy import EasyTask
from graders.support_grader import SupportGrader


def test_environment_initialization():
    """Test environment initialization."""
    env = Environment(EasyTask(), SupportGrader(), max_steps=100)
    assert env.max_steps == 100
    assert env.current_step == 0
    assert env.done == False


def test_environment_reset():
    """Test environment reset."""
    env = Environment(EasyTask(), SupportGrader())
    obs = env.reset()
    assert obs is not None
    assert env.current_step == 0
    assert env.done == False
    assert env.state() is not None


def test_environment_step():
    """Test environment step."""
    env = Environment(EasyTask(), SupportGrader())
    env.reset()
    act = Action(tool_name="test_action", tool_args={})
    obs, reward, done, info = env.step(act)
    assert obs is not None
    assert getattr(reward, 'value', None) is not None
    assert isinstance(done, bool)
    assert isinstance(info, dict)
