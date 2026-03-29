"""Deterministic grader for the Customer Support environment.

Scoring per step:
    Easy:   send_password_reset (+0.9) → close_ticket (+0.3)
    Medium: request_logs (+0.4) → reply w/ denial (+0.9)
    Hard:   request_logs (+0.7) → reply w/ v2.1 fix (+0.9) → close (+0.4)

Normalization (per-task theoretical ceiling):
    Easy:   /1.30  →  perfect ≈ 0.92
    Medium: /1.55  →  perfect ≈ 0.84
    Hard:   /2.60  →  perfect ≈ 0.77

Penalties: wrong action -0.5, repeated action -0.3, extra step -0.1 each.
Episode auto-terminates at 3 wrong actions or 20 steps.
"""
from typing import Any, Dict
from .base_grader import BaseGrader
from env.models import State, Action, Reward
from .rewards import RewardCalculator

TASK_NORMALIZATION = {
    "easy_ticket_1": 1.30,
    "medium_ticket_1": 1.55,
    "hard_ticket_1": 2.60,
}


class SupportGrader(BaseGrader):
    """Grades each step deterministically and accumulates a normalized score."""

    def __init__(self, answer_key: Dict[str, Any] = None, policy: Dict[str, Any] = None):
        super().__init__()
        self.calculator = RewardCalculator()
        self.task_id = None
        self.step_count = 0
        self.wrong_action_count = 0
        self.last_action = None
        self.min_steps = {"easy_ticket_1": 2, "medium_ticket_1": 2, "hard_ticket_1": 3}
        self.hard_task_sequence = []

    def reset_episode(self) -> None:
        self.calculator.reset()
        self.task_id = None
        self.step_count = 0
        self.wrong_action_count = 0
        self.last_action = None
        self.hard_task_sequence = []

    def grade(self, state: State, action: Action, is_complete: bool) -> Reward:
        if not self.task_id:
            self.task_id = state.task_id

        self.step_count += 1
        step_reward = 0.0
        info = ""

        if state.task_id == "easy_ticket_1":
            step_reward, info = self._grade_easy(action)
        elif state.task_id == "medium_ticket_1":
            step_reward, info = self._grade_medium(action)
        elif state.task_id == "hard_ticket_1":
            step_reward, info = self._grade_hard(action)

        min_req = self.min_steps.get(state.task_id, 2)
        if self.step_count > min_req:
            step_reward -= 0.1 * (self.step_count - min_req)

        step_reward = max(-0.3, step_reward)
        self.calculator.total_reward += step_reward

        if self.wrong_action_count >= 3:
            is_complete = True
        if self.step_count > 20:
            is_complete = True

        self.scores.append(step_reward)
        self.last_action = action.tool_name

        norm = TASK_NORMALIZATION.get(state.task_id, 1.5)
        final_score = max(0.0, min(1.0, self.calculator.total_reward / norm))

        return Reward(value=round(final_score, 3), is_complete=is_complete, info=info)

    def _grade_easy(self, action: Action) -> tuple:
        if self.step_count == 1:
            if action.tool_name == "send_password_reset":
                if action.tool_args.get("email") == "john@example.com":
                    return 0.9, "Sent password reset (+0.9)"
                return -0.5, "Wrong email (-0.5)"
            self.wrong_action_count += 1
            return -0.5, f"Wrong action: {action.tool_name} (-0.5)"

        if action.tool_name == "close_ticket":
            return 0.3, "Closed ticket (+0.3)"
        if action.tool_name == self.last_action:
            return -0.3, f"Repeated {action.tool_name} (-0.3)"
        self.wrong_action_count += 1
        return -0.5, f"Wrong action: {action.tool_name} (-0.5)"

    def _grade_medium(self, action: Action) -> tuple:
        if self.step_count == 1:
            if action.tool_name == "request_logs":
                return 0.4, "Checked policy (+0.4)"
            if action.tool_name == "reply_to_customer":
                content = str(action.tool_args.get("content", "")).lower()
                if any(kw in content for kw in ["deny", "cannot", "30"]):
                    return 0.7, "Direct denial (+0.7)"
                return -0.5, "Wrong response (-0.5)"
            if action.tool_name == "issue_refund":
                self.wrong_action_count += 3
                return -0.5, "POLICY VIOLATION (-0.5)"
            self.wrong_action_count += 1
            return -0.5, f"{action.tool_name} (-0.5)"

        if action.tool_name == "reply_to_customer":
            content = str(action.tool_args.get("content", "")).lower()
            if any(kw in content for kw in ["deny", "cannot", "30"]):
                return 0.9, "Proper denial (+0.9)"
            return -0.5, "Weak denial (-0.5)"
        if action.tool_name == "issue_refund":
            self.wrong_action_count += 3
            return -0.5, "POLICY VIOLATION (-0.5)"
        if action.tool_name == self.last_action:
            return -0.3, f"Repeated action (-0.3)"
        self.wrong_action_count += 1
        return -0.5, f"{action.tool_name} (-0.5)"

    def _grade_hard(self, action: Action) -> tuple:
        self.hard_task_sequence.append(action.tool_name)

        if self.step_count == 1:
            if action.tool_name == "request_logs":
                return 0.7, "Requested logs (+0.7)"
            self.wrong_action_count += 1
            return -0.5, "Must request logs first (-0.5)"

        if self.step_count == 2:
            if action.tool_name == "reply_to_customer":
                content = str(action.tool_args.get("content", "")).lower()
                if "v2.1" in content or "update client" in content:
                    return 0.9, "Correct diagnosis: v2.1 (+0.9)"
                self.wrong_action_count += 1
                return -0.5, "Wrong diagnosis (-0.5)"
            self.wrong_action_count += 1
            return -0.5, "Expected reply_to_customer (-0.5)"

        if action.tool_name == "close_ticket":
            return 0.4, "Closed ticket (+0.4)"
        if action.tool_name == "reply_to_customer":
            content = str(action.tool_args.get("content", "")).lower()
            if "v2.1" in content or "update client" in content:
                return 0.6, "Late diagnosis (+0.6)"
            return -0.3, "Extra communication (-0.3)"
        if action.tool_name == self.last_action:
            return -0.3, "Repeated action (-0.3)"
        return -0.5, f"{action.tool_name} (-0.5)"

    def get_final_score(self) -> float:
        return self.calculator.get_score(max_reward=2.5)
