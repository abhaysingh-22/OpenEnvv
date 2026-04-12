"""Core environment — manages task execution and the step/reset/state loop using OpenEnv framework."""
import json
import uuid
from pathlib import Path
from typing import Optional

from openenv.core.env_server import Environment
from support_env.models import SupportAction, SupportObservation, SupportState


# ──────────────────────────────────────────────────────────────────────────────
# Load data/ files — used by grading instead of hardcoded values
# ──────────────────────────────────────────────────────────────────────────────
DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"


def _load_json(filename):
    path = DATA_DIR / filename
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return {}


def _load_forbidden_phrases():
    path = DATA_DIR / "forbidden_phrases.txt"
    if path.exists():
        lines = path.read_text(encoding="utf-8").strip().split("\n")
        return [l.strip().lower() for l in lines if l.strip() and not l.startswith("#")]
    return []


COMPANY_POLICY = _load_json("company_policy.json")
ANSWER_KEYS = _load_json("answer_keys.json")
FORBIDDEN_PHRASES = _load_forbidden_phrases()

# Extract policy values from data files instead of hardcoding
REFUND_POLICY_DAYS = COMPANY_POLICY.get("refund_policy", {}).get("days_for_refund", 30)

# ──────────────────────────────────────────────────────────────────────────────
# Ticket definitions (data-driven)
# ──────────────────────────────────────────────────────────────────────────────
TICKETS = {
    # ── Easy tickets ──────────────────────────────────────────────────────
    "easy_ticket_1": {
        "type": "password_reset",
        "ticket_id": "TKT-1001",
        "user_name": "John Doe",
        "user_email": "john@example.com",
        "subject": "Cannot login, forgot password",
        "body": "Hi support, I forgot my password and cannot access my account. Please help.",
        "system_data": {"account_status": "active"},
    },
    "easy_ticket_2": {
        "type": "password_reset",
        "ticket_id": "TKT-1002",
        "user_name": "Sarah Chen",
        "user_email": "sarah.chen@example.com",
        "subject": "Account locked after failed attempts",
        "body": "I tried logging in several times and now my account is locked. Can you reset my password?",
        "system_data": {"account_status": "locked", "failed_attempts": 5},
    },
    # ── Medium tickets ────────────────────────────────────────────────────
    "medium_ticket_1": {
        "type": "policy_check",
        "ticket_id": "TKT-2001",
        "user_name": "Alice Smith",
        "user_email": "alice@example.com",
        "subject": "Requesting a refund",
        "body": "I bought this 40 days ago but I haven't used it. I want a refund.",
        "system_data": {
            "purchase_date": "2026-02-10",
            "current_date": "2026-03-27",
            "days_since_purchase": 45,
            "refund_policy_days": REFUND_POLICY_DAYS,
        },
        "policy_action": "deny",
        "policy_keywords": ["deny", "cannot", "policy", str(REFUND_POLICY_DAYS)],
    },
    "medium_ticket_2": {
        "type": "policy_check",
        "ticket_id": "TKT-2002",
        "user_name": "Dave Wilson",
        "user_email": "dave.wilson@example.com",
        "subject": "Warranty replacement request",
        "body": "My product stopped working. It's been about 3 months. Can I get a replacement under warranty?",
        "system_data": {
            "purchase_date": "2025-12-20",
            "current_date": "2026-03-27",
            "days_since_purchase": 97,
            "warranty_days": 90,
            "refund_policy_days": REFUND_POLICY_DAYS,
        },
        "policy_action": "deny",
        "policy_keywords": ["deny", "cannot", "expired", "90"],
    },
    # ── Hard tickets ──────────────────────────────────────────────────────
    "hard_ticket_1": {
        "type": "diagnostic",
        "ticket_id": "TKT-3001",
        "user_name": "Bob Jones",
        "user_email": "bob@example.com",
        "subject": "API is crashing",
        "body": "Every time I hit the /process endpoint, your API returns a 500 error. This is blocking our integration. Please fix ASAP.",
        "system_data": {
            "known_issues": {"ERR-99": "Fix: Update client to v2.1", "ERR-42": "Fix: Clear cache"},
            "error_code": "ERR-99",
        },
        "error_code": "ERR-99",
        "fix_keyword": "v2.1",
        "log_output": "[ERROR] Connection refused at 2026-03-27 14:32:15\nCode: ERR-99\nClient Version: v2.0.5",
    },
    "hard_ticket_2": {
        "type": "diagnostic",
        "ticket_id": "TKT-3002",
        "user_name": "Carol White",
        "user_email": "carol@example.com",
        "subject": "Data export timing out",
        "body": "Our nightly CSV export keeps failing with a timeout. We've tried increasing the timeout on our side but it still fails.",
        "system_data": {
            "known_issues": {"ERR-42": "Fix: Clear cache", "ERR-99": "Fix: Update client to v2.1"},
            "error_code": "ERR-42",
        },
        "error_code": "ERR-42",
        "fix_keyword": "clear cache",
        "log_output": "[ERROR] Operation timed out at 2026-03-27 03:15:42\nCode: ERR-42\nCache Size: 98% full",
    },
}

# Normalization constants per task (set above achievable max so no agent gets 1.0)
TASK_NORMALIZATION = {
    "easy_ticket_1": 1.25, "easy_ticket_2": 1.25,
    "medium_ticket_1": 1.40, "medium_ticket_2": 1.40,
    "hard_ticket_1": 1.80, "hard_ticket_2": 1.80,
}


def _check_forbidden_phrases(content: str) -> float:
    """Check reply content against forbidden phrases. Returns penalty (0.0 or negative)."""
    content_lower = content.lower()
    for phrase in FORBIDDEN_PHRASES:
        if phrase in content_lower:
            return -0.2  # Penalty for using forbidden language
    return 0.0


def _check_keyword_quality(content: str, required_keyword: str) -> float:
    """Anti-keyword-stuffing: keyword must appear in a constructive sentence, not with hedging."""
    content_lower = content.lower()
    if required_keyword.lower() not in content_lower:
        return 0.0  # Keyword not present at all
    # Check for hedging/confusion phrases that indicate the agent is guessing
    hedging = ["i don't know", "i'm not sure", "maybe", "i think", "possibly", "not certain", "unclear"]
    for hedge in hedging:
        if hedge in content_lower:
            return 0.5  # Partial credit — keyword present but agent is hedging
    return 1.0  # Full credit — keyword present, no hedging


class SupportEnvironment(Environment):
    """OpenEnv environment for customer support tasks."""

    def __init__(self):
        super().__init__()
        self._state = SupportState(task_id="easy_ticket_1")
        self._current_obs: Optional[SupportObservation] = None
        self._total_reward = 0.0
        self._wrong_action_count = 0
        self._last_action: Optional[str] = None
        self._hard_task_sequence = []
        self._ticket_config = None

        # Task specific states
        self._reset_sent = False
        self._policy_checked = False
        self._policy_response_given = False
        self._logs_requested = False
        self._solution_provided = False

    def reset(self, task_id: str = "easy_ticket_1", seed: int = None, episode_id: str = None, **kwargs) -> SupportObservation:
        """Reset to initial state and return the first observation."""
        if task_id not in TICKETS:
            raise ValueError(f"Unknown task_id: {task_id}. Available: {list(TICKETS.keys())}")

        if episode_id is None:
            episode_id = str(uuid.uuid4())

        self._state = SupportState(task_id=task_id, episode_id=episode_id, step_count=0)
        self._total_reward = 0.0
        self._wrong_action_count = 0
        self._last_action = None
        self._hard_task_sequence = []

        # Reset task flags
        self._reset_sent = False
        self._policy_checked = False
        self._policy_response_given = False
        self._logs_requested = False
        self._solution_provided = False

        # Load ticket config from data-driven definitions
        self._ticket_config = TICKETS[task_id]

        self._current_obs = SupportObservation(
            ticket_id=self._ticket_config["ticket_id"],
            user_name=self._ticket_config["user_name"],
            user_email=self._ticket_config["user_email"],
            subject=self._ticket_config["subject"],
            body=self._ticket_config["body"],
            history=[],
            system_data=self._ticket_config["system_data"],
        )

        return self._current_obs.model_copy(deep=True)

    def step(self, action: SupportAction) -> SupportObservation:
        """Execute one action and compute state transition + reward."""
        if self._current_obs is None or self._current_obs.done:
            raise RuntimeError("Episode is done or uninitialized. Call reset() first.")

        self._state.step_count += 1
        step_count = self._state.step_count
        task_id = self._state.task_id
        task_type = self._ticket_config["type"]

        # Track history
        history_updates = [{"agent": action.model_dump()}]

        # ──────────────────────────────────────────────────────────────────────
        # Transition Logic (by task TYPE, not individual task_id)
        # ──────────────────────────────────────────────────────────────────────
        is_complete = False

        if task_type == "password_reset":
            target_email = self._ticket_config["user_email"]
            if step_count == 1:
                if action.tool_name == "send_password_reset" and action.tool_args.get("email") == target_email:
                    self._reset_sent = True
                    history_updates.append({"user": "Thanks, I received the password reset link. Let me try logging in."})
                elif action.tool_name == "reply_to_customer":
                    history_updates.append({"user": "I just need a password reset link, please."})
                elif action.tool_name == "close_ticket":
                    history_updates.append({"system": "Cannot close without addressing issue."})
                else:
                    history_updates.append({"system": f"Acknowledged action: {action.tool_name}"})
            elif step_count >= 2:
                if action.tool_name == "close_ticket":
                    if self._reset_sent:
                        is_complete = True
                        history_updates.append({"system": "Ticket closed successfully."})
                    else:
                        history_updates.append({"system": "Cannot close - issue not resolved."})
                elif action.tool_name == "send_password_reset" and self._reset_sent:
                    history_updates.append({"system": "Password reset already sent."})
                elif action.tool_name == "reply_to_customer":
                    history_updates.append({"user": "Did you verify the reset link worked?"})
                else:
                    history_updates.append({"system": f"Acknowledged action: {action.tool_name}"})

        elif task_type == "policy_check":
            policy_keywords = self._ticket_config.get("policy_keywords", ["deny", "cannot", str(REFUND_POLICY_DAYS)])
            if step_count == 1:
                if action.tool_name == "request_logs":
                    self._policy_checked = True
                    sd = self._ticket_config["system_data"]
                    days = sd.get("days_since_purchase", "?")
                    limit = sd.get("refund_policy_days", sd.get("warranty_days", REFUND_POLICY_DAYS))
                    history_updates.append({"system": f"Policy Check: {limit}-day limit. Purchase was {days} days ago. DENY."})
                elif action.tool_name == "reply_to_customer":
                    content = str(action.tool_args.get("content", "")).lower()
                    if any(kw in content for kw in policy_keywords):
                        self._policy_response_given = True
                        history_updates.append({"user": "I understand, thank you for checking."})
                        is_complete = True
                    else:
                        history_updates.append({"user": "Does that mean I get a refund?"})
                elif action.tool_name == "issue_refund":
                    history_updates.append({"system": "ERROR: Refund issued outside policy window!"})
                else:
                    history_updates.append({"system": f"Acknowledged action: {action.tool_name}"})
            elif step_count >= 2:
                if action.tool_name == "reply_to_customer":
                    content = str(action.tool_args.get("content", "")).lower()
                    if any(kw in content for kw in policy_keywords):
                        self._policy_response_given = True
                        history_updates.append({"user": "I understand, thank you for checking."})
                        is_complete = True
                    else:
                        history_updates.append({"user": "I'm still confused."})
                elif action.tool_name == "issue_refund":
                    history_updates.append({"system": "ERROR: Policy violation!"})
                elif action.tool_name == "close_ticket":
                    if self._policy_response_given:
                        is_complete = True
                        history_updates.append({"system": "Ticket closed."})
                    else:
                        history_updates.append({"system": "Cannot close - issue not fully addressed."})
                elif action.tool_name == "request_logs":
                    if not self._policy_checked:
                        self._policy_checked = True
                        history_updates.append({"system": "Policy already checked."})
                    else:
                        history_updates.append({"system": "Policy already checked."})
                else:
                    history_updates.append({"system": f"Acknowledged action: {action.tool_name}"})

        elif task_type == "diagnostic":
            fix_keyword = self._ticket_config["fix_keyword"]
            log_output = self._ticket_config["log_output"]
            if step_count == 1:
                if action.tool_name == "request_logs":
                    self._logs_requested = True
                    history_updates.append({"system": f"Logs Retrieved:\n{log_output}"})
                elif action.tool_name == "reply_to_customer":
                    content = str(action.tool_args.get("content", "")).lower()
                    if fix_keyword.lower() in content:
                        self._solution_provided = True
                        history_updates.append({"user": "Thanks, let me try that."})
                    else:
                        history_updates.append({"user": "That doesn't make sense. Can you be more specific?"})
                else:
                    history_updates.append({"system": f"Acknowledged action: {action.tool_name}"})
            elif step_count >= 2:
                if action.tool_name == "reply_to_customer":
                    content = str(action.tool_args.get("content", "")).lower()
                    if fix_keyword.lower() in content:
                        self._solution_provided = True
                        if self._logs_requested:
                            history_updates.append({"user": "Perfect! That fixed it. Thank you!"})
                        else:
                            history_updates.append({"user": "Let me try that... it seems to work but I'm not sure why."})
                        if step_count >= 2:
                            is_complete = True
                    else:
                        history_updates.append({"user": "I tried that but it didn't work. Still getting the error."})
                elif action.tool_name == "request_logs":
                    if not self._logs_requested:
                        self._logs_requested = True
                        history_updates.append({"system": f"Logs Retrieved:\n{log_output}"})
                    else:
                        history_updates.append({"system": "Logs already retrieved."})
                elif action.tool_name == "close_ticket":
                    if self._solution_provided:
                        is_complete = True
                        history_updates.append({"system": "Ticket closed successfully."})
                    else:
                        history_updates.append({"system": "Cannot close - solution not yet provided."})
                else:
                    history_updates.append({"system": f"Acknowledged action: {action.tool_name}"})

        # Update History
        self._current_obs.history.extend(history_updates)

        # ──────────────────────────────────────────────────────────────────────
        # Grading Logic (by task TYPE)
        # ──────────────────────────────────────────────────────────────────────
        step_reward = 0.0
        info_str = ""

        if task_type == "password_reset":
            target_email = self._ticket_config["user_email"]
            if step_count == 1:
                if action.tool_name == "send_password_reset":
                    if action.tool_args.get("email") == target_email:
                        step_reward, info_str = 0.9, "Sent password reset (+0.9)"
                    else:
                        step_reward, info_str = -0.5, "Wrong email (-0.5)"
                else:
                    self._wrong_action_count += 1
                    step_reward, info_str = -0.5, f"Wrong action: {action.tool_name} (-0.5)"
            else:
                if action.tool_name == "close_ticket":
                    step_reward, info_str = 0.3, "Closed ticket (+0.3)"
                elif action.tool_name == self._last_action:
                    step_reward, info_str = -0.3, f"Repeated {action.tool_name} (-0.3)"
                else:
                    self._wrong_action_count += 1
                    step_reward, info_str = -0.5, f"Wrong action: {action.tool_name} (-0.5)"

        elif task_type == "policy_check":
            policy_keywords = self._ticket_config.get("policy_keywords", ["deny", "cannot", str(REFUND_POLICY_DAYS)])
            if step_count == 1:
                if action.tool_name == "request_logs":
                    step_reward, info_str = 0.4, "Checked policy (+0.4)"
                elif action.tool_name == "reply_to_customer":
                    content = str(action.tool_args.get("content", "")).lower()
                    if any(kw in content for kw in policy_keywords):
                        step_reward, info_str = 0.7, "Direct denial (+0.7)"
                    else:
                        step_reward, info_str = -0.5, "Wrong response (-0.5)"
                    # Forbidden phrase check
                    step_reward += _check_forbidden_phrases(content)
                elif action.tool_name == "issue_refund":
                    self._wrong_action_count += 3
                    step_reward, info_str = -0.5, "POLICY VIOLATION (-0.5)"
                else:
                    self._wrong_action_count += 1
                    step_reward, info_str = -0.5, f"{action.tool_name} (-0.5)"
            else:
                if action.tool_name == "reply_to_customer":
                    content = str(action.tool_args.get("content", "")).lower()
                    if any(kw in content for kw in policy_keywords):
                        step_reward, info_str = 0.9, "Proper denial (+0.9)"
                    else:
                        step_reward, info_str = -0.5, "Weak denial (-0.5)"
                    step_reward += _check_forbidden_phrases(content)
                elif action.tool_name == "issue_refund":
                    self._wrong_action_count += 3
                    step_reward, info_str = -0.5, "POLICY VIOLATION (-0.5)"
                elif action.tool_name == self._last_action:
                    step_reward, info_str = -0.3, "Repeated action (-0.3)"
                else:
                    self._wrong_action_count += 1
                    step_reward, info_str = -0.5, f"{action.tool_name} (-0.5)"

        elif task_type == "diagnostic":
            fix_keyword = self._ticket_config["fix_keyword"]
            self._hard_task_sequence.append(action.tool_name)
            if step_count == 1:
                if action.tool_name == "request_logs":
                    step_reward, info_str = 0.7, "Requested logs (+0.7)"
                else:
                    self._wrong_action_count += 1
                    step_reward, info_str = -0.5, "Must request logs first (-0.5)"
            elif step_count == 2:
                if action.tool_name == "reply_to_customer":
                    content = str(action.tool_args.get("content", "")).lower()
                    quality = _check_keyword_quality(content, fix_keyword)
                    if quality >= 1.0:
                        step_reward, info_str = 0.9, f"Correct diagnosis: {fix_keyword} (+0.9)"
                    elif quality >= 0.5:
                        step_reward, info_str = 0.4, f"Hedged diagnosis ({fix_keyword} mentioned but uncertain) (+0.4)"
                    else:
                        self._wrong_action_count += 1
                        step_reward, info_str = -0.5, "Wrong diagnosis (-0.5)"
                    step_reward += _check_forbidden_phrases(content)
                else:
                    self._wrong_action_count += 1
                    step_reward, info_str = -0.5, "Expected reply_to_customer (-0.5)"
            else:
                if action.tool_name == "close_ticket":
                    step_reward, info_str = 0.4, "Closed ticket (+0.4)"
                elif action.tool_name == "reply_to_customer":
                    content = str(action.tool_args.get("content", "")).lower()
                    quality = _check_keyword_quality(content, fix_keyword)
                    if quality >= 1.0:
                        step_reward, info_str = 0.6, "Late diagnosis (+0.6)"
                    elif quality >= 0.5:
                        step_reward, info_str = 0.3, "Hedged late diagnosis (+0.3)"
                    else:
                        step_reward, info_str = -0.3, "Extra communication (-0.3)"
                    step_reward += _check_forbidden_phrases(content)
                elif action.tool_name == self._last_action:
                    step_reward, info_str = -0.3, "Repeated action (-0.3)"
                else:
                    step_reward, info_str = -0.5, f"{action.tool_name} (-0.5)"

        # Extra steps penalty
        min_steps = 3 if task_type == "diagnostic" else 2
        if step_count > min_steps:
            step_reward -= 0.1 * (step_count - min_steps)

        step_reward = max(-0.3, step_reward)
        self._total_reward += step_reward

        # Termination conditions
        if self._wrong_action_count >= 3 or step_count > 20:
            is_complete = True

        self._last_action = action.tool_name

        # Final normalization to (0.0, 1.0) — strictly between 0 and 1 (exclusive)
        norm = TASK_NORMALIZATION.get(task_id, 1.5)
        final_score = max(0.01, min(0.99, self._total_reward / norm))

        # Update observation
        self._current_obs.done = is_complete
        self._current_obs.reward = round(final_score, 3)
        self._current_obs.metadata = {"info": info_str}

        return self._current_obs.model_copy(deep=True)

    @property
    def state(self) -> SupportState:
        """Return the current state snapshot."""
        return self._state.model_copy(deep=True)


