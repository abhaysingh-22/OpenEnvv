"""Tests for Pydantic models."""
import pytest
from support_env.models import SupportAction, SupportObservation, SupportState


def test_action_creation():
    """Test SupportAction creation with tool_name and tool_args."""
    action = SupportAction(tool_name="reply_to_customer", tool_args={"content": "Hello!"})
    assert action.tool_name == "reply_to_customer"
    assert action.tool_args["content"] == "Hello!"


def test_action_default_args():
    """Test SupportAction with default empty tool_args."""
    action = SupportAction(tool_name="close_ticket")
    assert action.tool_args == {}


def test_observation_creation():
    """Test SupportObservation creation with all fields."""
    obs = SupportObservation(
        ticket_id="TKT-001",
        user_name="Test User",
        user_email="test@example.com",
        subject="Test Subject",
        body="Test body"
    )
    assert obs.ticket_id == "TKT-001"
    assert obs.user_email == "test@example.com"
    assert obs.history == []
    assert obs.system_data == {}


def test_observation_with_history():
    """Test SupportObservation with history entries."""
    obs = SupportObservation(
        ticket_id="TKT-001",
        user_name="Test",
        user_email="t@t.com",
        subject="S",
        body="B",
        history=[{"agent": "some action"}, {"user": "response"}]
    )
    assert len(obs.history) == 2


def test_state_creation():
    """Test SupportState creation."""
    state = SupportState(task_id="easy_ticket_1")
    assert state.task_id == "easy_ticket_1"


def test_action_serialization():
    """Test that actions can be serialized to dict."""
    action = SupportAction(tool_name="send_password_reset", tool_args={"email": "a@b.com"})
    d = action.model_dump()
    assert d["tool_name"] == "send_password_reset"
    assert d["tool_args"]["email"] == "a@b.com"


def test_observation_serialization():
    """Test that observations can be serialized to dict."""
    obs = SupportObservation(
        ticket_id="T1", user_name="U", user_email="e@e.com",
        subject="S", body="B"
    )
    d = obs.model_dump()
    assert "ticket_id" in d
    assert "user_email" in d

