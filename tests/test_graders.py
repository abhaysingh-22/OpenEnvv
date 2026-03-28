"""Tests for the graders module."""
import pytest
from graders.support_grader import SupportGrader
from env.models import State, Action, Observation


def test_support_grader_initialization():
    """Test support grader initialization."""
    grader = SupportGrader()
    assert grader is not None
    assert grader.scores == []


def test_support_grader_grading():
    """Test support grader grading."""
    grader = SupportGrader()
    obs = Observation(ticket_id="1", user_name="A", user_email="a", subject="a", body="a")
    state = State(task_id="easy_ticket_1", step=1, observation=obs)
    
    act = Action(tool_name="send_password_reset", tool_args={"email": "john@example.com"})
    reward = grader.grade(state, act, is_complete=True)
    assert getattr(reward, 'value', None) is not None
    assert reward.value == 1.0


def test_score_history():
    """Test score history tracking."""
    grader = SupportGrader()
    obs = Observation(ticket_id="1", user_name="A", user_email="a", subject="a", body="a")
    state = State(task_id="easy_ticket_1", step=1, observation=obs)
    act = Action(tool_name="reply_to_customer", tool_args={})
    
    grader.grade(state, act, is_complete=True)
    grader.grade(state, act, is_complete=False)
    history = grader.get_score_history()
    assert len(history) == 2
