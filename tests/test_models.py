"""Tests for the models module."""
import pytest
from env.models import Task, Agent, State


def test_task_creation():
    """Test task creation."""
    task = Task(
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
        Task(
            id='task_1',
            title='Test Task',
            description='Test Description',
            difficulty='invalid'
        )


def test_agent_creation():
    """Test agent creation."""
    agent = Agent(
        id='agent_1',
        name='Test Agent',
        agent_type='dummy',
        config={}
    )
    assert agent.id == 'agent_1'
    assert agent.agent_type == 'dummy'


def test_state_creation():
    """Test state creation."""
    state = State(
        task_id='task_1',
        step=1,
        observation={'test': 'value'}
    )
    assert state.task_id == 'task_1'
    assert state.step == 1
    assert state.history == []
