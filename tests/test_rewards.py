"""Tests for reward accumulation and normalization."""
import pytest
from support_env.server.support_environment import SupportEnvironment
from support_env.models import SupportAction


def test_reward_accumulates_across_steps():
    """Reward should accumulate (grow) across correct steps."""
    env = SupportEnvironment()
    env.reset(task_id="easy_ticket_1")
    obs1 = env.step(SupportAction(tool_name="send_password_reset", tool_args={"email": "john@example.com"}))
    obs2 = env.step(SupportAction(tool_name="close_ticket", tool_args={}))
    assert obs2.reward > obs1.reward, "Reward should increase after closing ticket"


def test_penalty_reduces_reward():
    """Wrong actions should reduce the accumulated reward."""
    env = SupportEnvironment()
    env.reset(task_id="easy_ticket_1")
    obs = env.step(SupportAction(tool_name="issue_refund", tool_args={}))
    assert obs.reward <= 0.01, f"Expected near 0 for wrong action, got {obs.reward}"


def test_reward_clamped_to_unit_range():
    """Reward should never exceed 1.0 or go below 0.0."""
    env = SupportEnvironment()
    for task_id in ["easy_ticket_1", "medium_ticket_1", "hard_ticket_1"]:
        env.reset(task_id=task_id)
        for _ in range(5):
            obs = env.step(SupportAction(tool_name="close_ticket", tool_args={}))
            assert 0.0 < obs.reward < 1.0, f"Reward {obs.reward} out of range for {task_id}"
            if obs.done:
                break


def test_partial_reward_signal():
    """Partial progress should produce non-zero reward before completion."""
    env = SupportEnvironment()
    env.reset(task_id="hard_ticket_1")
    obs = env.step(SupportAction(tool_name="request_logs", tool_args={}))
    assert obs.reward > 0.0, "request_logs should produce partial reward"
    assert obs.done is False, "Episode should not be done after first step"


def test_repeated_action_penalty():
    """Repeating the same action should be penalized."""
    env = SupportEnvironment()
    env.reset(task_id="easy_ticket_1")
    obs1 = env.step(SupportAction(tool_name="send_password_reset", tool_args={"email": "john@example.com"}))
    obs2 = env.step(SupportAction(tool_name="send_password_reset", tool_args={"email": "john@example.com"}))
    # Second send should not increase the score (repeated action penalty)
    assert obs2.reward <= obs1.reward, "Repeated action should not increase reward"


