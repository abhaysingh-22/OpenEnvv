"""Tests for the SupportEnvironment (step/reset/state loop)."""
import pytest
from support_env.server.support_environment import SupportEnvironment
from support_env.models import SupportAction


def test_environment_reset_easy():
    """Test reset() returns a valid initial observation for easy task."""
    env = SupportEnvironment()
    obs = env.reset(task_id="easy_ticket_1")
    assert obs is not None
    assert obs.ticket_id == "TKT-1001"
    assert obs.user_email == "john@example.com"
    assert obs.done is False or obs.done is None


def test_environment_reset_medium():
    """Test reset() returns a valid initial observation for medium task."""
    env = SupportEnvironment()
    obs = env.reset(task_id="medium_ticket_1")
    assert obs.ticket_id == "TKT-2001"
    assert obs.system_data["days_since_purchase"] == 45


def test_environment_reset_hard():
    """Test reset() returns a valid initial observation for hard task."""
    env = SupportEnvironment()
    obs = env.reset(task_id="hard_ticket_1")
    assert obs.ticket_id == "TKT-3001"
    assert obs.system_data["error_code"] == "ERR-99"


def test_environment_reset_unknown_task():
    """Test reset() raises ValueError for unknown task."""
    env = SupportEnvironment()
    with pytest.raises(ValueError, match="Unknown task_id"):
        env.reset(task_id="nonexistent_task")


def test_environment_step_returns_observation():
    """Test step() returns a valid observation with reward."""
    env = SupportEnvironment()
    env.reset(task_id="easy_ticket_1")
    action = SupportAction(tool_name="send_password_reset", tool_args={"email": "john@example.com"})
    obs = env.step(action)
    assert obs is not None
    assert obs.reward is not None
    assert isinstance(obs.reward, float)


def test_environment_state_property():
    """Test state property returns current state."""
    env = SupportEnvironment()
    env.reset(task_id="easy_ticket_1")
    state = env.state
    assert state.task_id == "easy_ticket_1"
    assert state.step_count == 0


def test_step_before_reset_raises():
    """Test step() raises when called without reset()."""
    env = SupportEnvironment()
    action = SupportAction(tool_name="close_ticket", tool_args={})
    with pytest.raises(RuntimeError):
        env.step(action)


def test_episode_terminates_on_done():
    """Test that episode terminates correctly."""
    env = SupportEnvironment()
    env.reset(task_id="easy_ticket_1")
    # Step 1: correct password reset
    obs = env.step(SupportAction(tool_name="send_password_reset", tool_args={"email": "john@example.com"}))
    assert obs.done is False
    # Step 2: close ticket
    obs = env.step(SupportAction(tool_name="close_ticket", tool_args={}))
    assert obs.done is True
