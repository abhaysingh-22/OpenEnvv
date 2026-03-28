"""Tests for the models module."""
import pytest
from env.models import TaskConfig, AgentConfig, State, Observation, Action


def test_task_creation():
    """Test task configuration creation."""
    task = TaskConfig(
        id='task_1',
        title='Test Task',
        description='Test Description',
        difficulty='easy'
    )
    assert task.id == 'task_1'
    assert task.difficulty == 'easy'


def test_task_invalid_difficulty():
    """Test task with invalid difficulty."""
    with pytest.raises(ValueError):
        task = TaskConfig(
            id='task_1',
            title='Test Task',
            description='Test Description',
            difficulty='invalid'
        )
        task.validate_difficulty()


def test_observation_creation():
    """Test observation creation."""
    obs = Observation(ticket_id="1", user_name="A", user_email="a@a.com", subject="S", body="B")
    assert obs.ticket_id == "1"
    assert obs.history == []


def test_action_creation():
    """Test action creation."""
    act = Action(tool_name="reply", tool_args={"msg": "hi"})
    assert act.tool_name == "reply"
    assert act.tool_args["msg"] == "hi"


def test_state_creation():
    """Test state creation."""
    obs = Observation(ticket_id="1", user_name="A", user_email="a@a.com", subject="S", body="B")
    state = State(
        task_id='task_1',
        step=1,
        observation=obs
    )
    assert state.task_id == 'task_1'
    assert state.step == 1
