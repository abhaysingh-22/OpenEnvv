"""Tests for grading logic embedded in SupportEnvironment."""
import pytest
from support_env.server.support_environment import SupportEnvironment
from support_env.models import SupportAction


def test_easy_correct_sequence_scores_high():
    """Perfect agent on easy task should score ~1.0."""
    env = SupportEnvironment()
    env.reset(task_id="easy_ticket_1")
    obs = env.step(SupportAction(tool_name="send_password_reset", tool_args={"email": "john@example.com"}))
    obs = env.step(SupportAction(tool_name="close_ticket", tool_args={}))
    assert 0.85 <= obs.reward < 1.0, f"Expected ~0.96 (high but not perfect), got {obs.reward}"
    assert obs.done is True


def test_easy_wrong_email_penalises():
    """Wrong email should get a penalty."""
    env = SupportEnvironment()
    env.reset(task_id="easy_ticket_1")
    obs = env.step(SupportAction(tool_name="send_password_reset", tool_args={"email": "wrong@example.com"}))
    assert obs.reward < 0.5, f"Expected low score for wrong email, got {obs.reward}"


def test_medium_policy_denial_scores_high():
    """Correctly denying refund with policy reference should score well."""
    env = SupportEnvironment()
    env.reset(task_id="medium_ticket_1")
    obs = env.step(SupportAction(tool_name="request_logs", tool_args={}))
    obs = env.step(SupportAction(tool_name="reply_to_customer", tool_args={
        "content": "Your purchase exceeds our 30-day refund window. We cannot process this refund."
    }))
    assert 0.75 <= obs.reward < 1.0, f"Expected ~0.93 (high but not perfect), got {obs.reward}"


def test_medium_issue_refund_is_policy_violation():
    """Issuing refund outside 30-day window should trigger severe penalty."""
    env = SupportEnvironment()
    env.reset(task_id="medium_ticket_1")
    obs = env.step(SupportAction(tool_name="issue_refund", tool_args={}))
    assert obs.reward < 0.2, f"Expected low score for policy violation, got {obs.reward}"


def test_hard_correct_sequence_scores_high():
    """Perfect agent on hard task: request_logs → reply(v2.1) should score 1.0."""
    env = SupportEnvironment()
    env.reset(task_id="hard_ticket_1")
    obs = env.step(SupportAction(tool_name="request_logs", tool_args={}))
    obs = env.step(SupportAction(tool_name="reply_to_customer", tool_args={
        "content": "The logs show ERR-99. Please update your client to v2.1 to resolve this."
    }))
    assert 0.80 <= obs.reward < 1.0, f"Expected ~0.89 (high but not perfect), got {obs.reward}"
    assert obs.done is True


def test_scores_in_valid_range():
    """All scores should be in [0.0, 1.0]."""
    env = SupportEnvironment()
    for task_id in ["easy_ticket_1", "medium_ticket_1", "hard_ticket_1"]:
        env.reset(task_id=task_id)
        obs = env.step(SupportAction(tool_name="close_ticket", tool_args={}))
        assert 0.0 <= obs.reward <= 1.0, f"Score {obs.reward} out of [0,1] for {task_id}"


def test_score_differentiation():
    """Perfect agent should score higher than random actions."""
    env = SupportEnvironment()

    # Perfect easy
    env.reset(task_id="easy_ticket_1")
    env.step(SupportAction(tool_name="send_password_reset", tool_args={"email": "john@example.com"}))
    perfect_obs = env.step(SupportAction(tool_name="close_ticket", tool_args={}))

    # Random easy
    env.reset(task_id="easy_ticket_1")
    random_obs = env.step(SupportAction(tool_name="issue_refund", tool_args={}))

    assert perfect_obs.reward > random_obs.reward
