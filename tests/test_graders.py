"""Tests for the grading logic embedded in SupportEnvironment."""
import pytest
from support_env.server.support_environment import SupportEnvironment, FORBIDDEN_PHRASES
from support_env.models import SupportAction


def test_easy_correct_sequence_scores_high():
    """Perfect agent on easy task: send_password_reset → close_ticket should score ~0.96."""
    env = SupportEnvironment()
    env.reset(task_id="easy_ticket_1")
    obs = env.step(SupportAction(tool_name="send_password_reset", tool_args={"email": "john@example.com"}))
    obs = env.step(SupportAction(tool_name="close_ticket", tool_args={}))
    assert 0.85 <= obs.reward < 0.99, f"Expected ~0.96 (high but not perfect), got {obs.reward}"
    assert obs.done is True


def test_easy_2_correct_sequence_scores_high():
    """Perfect agent on easy_ticket_2: send_password_reset(sarah) → close_ticket."""
    env = SupportEnvironment()
    env.reset(task_id="easy_ticket_2")
    obs = env.step(SupportAction(tool_name="send_password_reset", tool_args={"email": "sarah.chen@example.com"}))
    obs = env.step(SupportAction(tool_name="close_ticket", tool_args={}))
    assert 0.85 <= obs.reward < 0.99, f"Expected ~0.96 (high but not perfect), got {obs.reward}"
    assert obs.done is True


def test_easy_wrong_email_penalises():
    """Wrong email address should reduce reward."""
    env = SupportEnvironment()
    env.reset(task_id="easy_ticket_1")
    obs = env.step(SupportAction(tool_name="send_password_reset", tool_args={"email": "wrong@test.com"}))
    assert obs.reward < 0.5, f"Wrong email should score low, got {obs.reward}"


def test_medium_policy_denial_scores_high():
    """Perfect agent on medium: request_logs → reply with denial → high score."""
    env = SupportEnvironment()
    env.reset(task_id="medium_ticket_1")
    obs = env.step(SupportAction(tool_name="request_logs", tool_args={}))
    obs = env.step(SupportAction(tool_name="reply_to_customer", tool_args={
        "content": "Your purchase exceeds our 30-day refund window. We cannot process this refund."
    }))
    assert 0.75 <= obs.reward < 0.99, f"Expected ~0.93 (high but not perfect), got {obs.reward}"


def test_medium_2_warranty_denial_scores_high():
    """Perfect agent on medium_ticket_2: request_logs → reply with warranty denial."""
    env = SupportEnvironment()
    env.reset(task_id="medium_ticket_2")
    obs = env.step(SupportAction(tool_name="request_logs", tool_args={}))
    obs = env.step(SupportAction(tool_name="reply_to_customer", tool_args={
        "content": "Your product is past the 90-day warranty period. We cannot approve a replacement."
    }))
    assert 0.75 <= obs.reward < 0.99, f"Expected high score for correct warranty denial, got {obs.reward}"


def test_medium_issue_refund_is_policy_violation():
    """Using issue_refund outside policy window should trigger instant failure."""
    env = SupportEnvironment()
    env.reset(task_id="medium_ticket_1")
    obs = env.step(SupportAction(tool_name="issue_refund", tool_args={}))
    assert obs.reward <= 0.05, f"Expected near minimum for policy violation, got {obs.reward}"


def test_hard_correct_sequence_scores_high():
    """Perfect agent on hard task: request_logs → reply(v2.1) should score high (not 0.999)."""
    env = SupportEnvironment()
    env.reset(task_id="hard_ticket_1")
    obs = env.step(SupportAction(tool_name="request_logs", tool_args={}))
    obs = env.step(SupportAction(tool_name="reply_to_customer", tool_args={
        "content": "The logs show ERR-99. Please update your client to v2.1 to resolve this."
    }))
    assert 0.80 <= obs.reward < 0.99, f"Expected ~0.89 (high but not perfect), got {obs.reward}"
    assert obs.done is True


def test_hard_2_correct_sequence_scores_high():
    """Perfect agent on hard_ticket_2: request_logs → reply(clear cache)."""
    env = SupportEnvironment()
    env.reset(task_id="hard_ticket_2")
    obs = env.step(SupportAction(tool_name="request_logs", tool_args={}))
    obs = env.step(SupportAction(tool_name="reply_to_customer", tool_args={
        "content": "The logs show ERR-42. Your cache is 98% full. Please clear cache to resolve the timeout."
    }))
    assert 0.80 <= obs.reward < 0.99, f"Expected high score for correct ERR-42 diagnosis, got {obs.reward}"
    assert obs.done is True


def test_hard_keyword_stuffing_with_hedging():
    """Keyword-stuffing with hedging phrases should get lower score."""
    env = SupportEnvironment()
    env.reset(task_id="hard_ticket_1")
    obs = env.step(SupportAction(tool_name="request_logs", tool_args={}))
    obs = env.step(SupportAction(tool_name="reply_to_customer", tool_args={
        "content": "I'm not sure, maybe try v2.1 but I don't know if it will help."
    }))
    # Should get partial credit (hedging detected), not full 0.9
    assert obs.reward < 0.8, f"Hedged response should score lower than confident one, got {obs.reward}"


def test_scores_in_valid_range():
    """All task scores must be strictly between 0 and 1 (0.001 to 0.999)."""
    for task_id in ["easy_ticket_1", "easy_ticket_2", "medium_ticket_1", "medium_ticket_2", "hard_ticket_1", "hard_ticket_2"]:
        env = SupportEnvironment()
        env.reset(task_id=task_id)
        obs = env.step(SupportAction(tool_name="close_ticket", tool_args={}))
        assert 0.001 <= obs.reward <= 0.999, f"Score {obs.reward} out of range (0.001-0.999) for {task_id}"


def test_score_differentiation():
    """Perfect agent should score higher than wrong actions across all tasks."""
    for task_id, email in [("easy_ticket_1", "john@example.com"), ("easy_ticket_2", "sarah.chen@example.com")]:
        env_good = SupportEnvironment()
        env_good.reset(task_id=task_id)
        obs_good = env_good.step(SupportAction(tool_name="send_password_reset", tool_args={"email": email}))
        obs_good = env_good.step(SupportAction(tool_name="close_ticket", tool_args={}))

        env_bad = SupportEnvironment()
        env_bad.reset(task_id=task_id)
        obs_bad = env_bad.step(SupportAction(tool_name="close_ticket", tool_args={}))

        assert obs_good.reward > obs_bad.reward, f"Perfect should beat bad in {task_id}"


def test_forbidden_phrases_loaded():
    """Verify forbidden phrases are loaded from data/forbidden_phrases.txt."""
    assert len(FORBIDDEN_PHRASES) > 0, "Forbidden phrases should be loaded from data/"
    assert "your fault" in FORBIDDEN_PHRASES, "'your fault' should be a forbidden phrase"


