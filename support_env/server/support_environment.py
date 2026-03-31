"""Core environment — manages task execution and the step/reset/state loop using OpenEnv framework."""
import uuid
from typing import Optional

from openenv.core.env_server import Environment
from support_env.models import SupportAction, SupportObservation, SupportState


# ──────────────────────────────────────────────────────────────────────────────
# We inline the Grader and Task logic directly into the Environment to keep it 
# cohesive with OpenEnv's single-class pattern (like chess_env).
# ──────────────────────────────────────────────────────────────────────────────

TASK_NORMALIZATION = {
    "easy_ticket_1": 1.25,
    "medium_ticket_1": 1.40,
    "hard_ticket_1": 1.80,
}

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
        
        # Task specific states
        self._reset_sent = False
        self._policy_checked = False
        self._policy_response_given = False
        self._logs_requested = False
        self._solution_provided = False

    def reset(self, task_id: str = "easy_ticket_1", seed: int = None, episode_id: str = None, **kwargs) -> SupportObservation:
        """Reset to initial state and return the first observation."""
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
        
        if task_id == "easy_ticket_1":
            self._current_obs = SupportObservation(
                ticket_id="TKT-1001",
                user_name="John Doe",
                user_email="john@example.com",
                subject="Cannot login, forgot password",
                body="Hi support, I forgot my password and cannot access my account. Please help.",
                history=[],
                system_data={"account_status": "active"},
            )
        elif task_id == "medium_ticket_1":
            self._current_obs = SupportObservation(
                ticket_id="TKT-2001",
                user_name="Alice Smith",
                user_email="alice@example.com",
                subject="Requesting a refund",
                body="I bought this 40 days ago but I haven't used it. I want a refund.",
                history=[],
                system_data={
                    "purchase_date": "2026-02-10",
                    "current_date": "2026-03-27",
                    "days_since_purchase": 45,
                    "refund_policy_days": 30,
                },
            )
        elif task_id == "hard_ticket_1":
            self._current_obs = SupportObservation(
                ticket_id="TKT-3001",
                user_name="Bob Jones",
                user_email="bob@example.com",
                subject="API is crashing",
                body="Every time I hit the /process endpoint, your API returns a 500 error. This is blocking our integration. Please fix ASAP.",
                history=[],
                system_data={
                    "known_issues": {
                        "ERR-99": "Fix: Update client to v2.1",
                        "ERR-42": "Fix: Clear cache",
                    },
                    "error_code": "ERR-99",
                },
            )
        else:
            raise ValueError(f"Unknown task_id: {task_id}")
            
        return self._current_obs.model_copy(deep=True)

    def step(self, action: SupportAction) -> SupportObservation:
        """Execute one action and compute state transition + reward."""
        if self._current_obs is None or self._current_obs.done:
            raise RuntimeError("Episode is done or uninitialized. Call reset() first.")

        self._state.step_count += 1
        step_count = self._state.step_count
        task_id = self._state.task_id
        
        # Track history
        history_updates = [{"agent": action.model_dump()}]
        
        # ──────────────────────────────────────────────────────────────────────
        # Transition Logic
        # ──────────────────────────────────────────────────────────────────────
        is_complete = False
        
        if task_id == "easy_ticket_1":
            if step_count == 1:
                if action.tool_name == "send_password_reset" and action.tool_args.get("email") == "john@example.com":
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
                    
        elif task_id == "medium_ticket_1":
            if step_count == 1:
                if action.tool_name == "request_logs":
                    self._policy_checked = True
                    history_updates.append({"system": "Policy Check: 30-day refund limit. Purchase was 45 days ago. DENY refund."})
                elif action.tool_name == "reply_to_customer":
                    content = str(action.tool_args.get("content", "")).lower()
                    if any(kw in content for kw in ["deny", "policy", "cannot", "30"]):
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
                    if any(kw in content for kw in ["deny", "policy", "cannot", "30"]):
                        self._policy_response_given = True
                        history_updates.append({"user": "I understand, thank you for checking."})
                        is_complete = True
                    else:
                        history_updates.append({"user": "I'm still confused about the refund."})
                elif action.tool_name == "issue_refund":
                    history_updates.append({"system": "ERROR: Refund policy violation!"})
                elif action.tool_name == "close_ticket":
                    if self._policy_response_given:
                        is_complete = True
                        history_updates.append({"system": "Ticket closed."})
                    else:
                        history_updates.append({"system": "Cannot close - issue not fully addressed."})
                elif action.tool_name == "request_logs":
                    if not self._policy_checked:
                        self._policy_checked = True
                        history_updates.append({"system": "Policy Check: 30-day refund limit. DENY refund."})
                    else:
                        history_updates.append({"system": "Policy already checked."})
                else:
                    history_updates.append({"system": f"Acknowledged action: {action.tool_name}"})
                    
        elif task_id == "hard_ticket_1":
            if step_count == 1:
                if action.tool_name == "request_logs":
                    self._logs_requested = True
                    history_updates.append({
                        "system": "Logs Retrieved:\n[ERROR] Connection refused at 2026-03-27 14:32:15\nCode: ERR-99\nClient Version: v2.0.5"
                    })
                elif action.tool_name == "reply_to_customer":
                    content = str(action.tool_args.get("content", "")).lower()
                    if "update client to v2.1" in content or "v2.1" in content:
                        self._solution_provided = True
                        history_updates.append({"user": "Got it! Let me update my client."})
                    else:
                        history_updates.append({"user": "That doesn't make sense. Can you be more specific?"})
                else:
                    history_updates.append({"system": f"Acknowledged action: {action.tool_name}"})
            elif step_count >= 2:
                if action.tool_name == "reply_to_customer":
                    content = str(action.tool_args.get("content", "")).lower()
                    if "update client to v2.1" in content or "v2.1" in content:
                        self._solution_provided = True
                        if self._logs_requested:
                            history_updates.append({"user": "Perfect! That fixed it. The /process endpoint is working now. Thank you!"})
                        else:
                            history_updates.append({"user": "Let me try that... actually, it's working now but I'm not sure why your suggestion helped."})
                        if step_count >= 2:
                            is_complete = True
                    else:
                        history_updates.append({"user": "I tried that but it didn't work. Still getting the 500 error."})
                elif action.tool_name == "request_logs":
                    if not self._logs_requested:
                        self._logs_requested = True
                        history_updates.append({"system": "Logs Retrieved:\n[ERROR] Connection refused.\nCode: ERR-99"})
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
        # Grading Logic
        # ──────────────────────────────────────────────────────────────────────
        step_reward = 0.0
        info_str = ""
        
        if task_id == "easy_ticket_1":
            if step_count == 1:
                if action.tool_name == "send_password_reset":
                    if action.tool_args.get("email") == "john@example.com":
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

        elif task_id == "medium_ticket_1":
            if step_count == 1:
                if action.tool_name == "request_logs":
                    step_reward, info_str = 0.4, "Checked policy (+0.4)"
                elif action.tool_name == "reply_to_customer":
                    content = str(action.tool_args.get("content", "")).lower()
                    if any(kw in content for kw in ["deny", "cannot", "30"]):
                        step_reward, info_str = 0.7, "Direct denial (+0.7)"
                    else:
                        step_reward, info_str = -0.5, "Wrong response (-0.5)"
                elif action.tool_name == "issue_refund":
                    self._wrong_action_count += 3
                    step_reward, info_str = -0.5, "POLICY VIOLATION (-0.5)"
                else:
                    self._wrong_action_count += 1
                    step_reward, info_str = -0.5, f"{action.tool_name} (-0.5)"
            else:
                if action.tool_name == "reply_to_customer":
                    content = str(action.tool_args.get("content", "")).lower()
                    if any(kw in content for kw in ["deny", "cannot", "30"]):
                        step_reward, info_str = 0.9, "Proper denial (+0.9)"
                    else:
                        step_reward, info_str = -0.5, "Weak denial (-0.5)"
                elif action.tool_name == "issue_refund":
                    self._wrong_action_count += 3
                    step_reward, info_str = -0.5, "POLICY VIOLATION (-0.5)"
                elif action.tool_name == self._last_action:
                    step_reward, info_str = -0.3, f"Repeated action (-0.3)"
                else:
                    self._wrong_action_count += 1
                    step_reward, info_str = -0.5, f"{action.tool_name} (-0.5)"

        elif task_id == "hard_ticket_1":
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
                    if "v2.1" in content or "update client" in content:
                        step_reward, info_str = 0.9, "Correct diagnosis: v2.1 (+0.9)"
                    else:
                        self._wrong_action_count += 1
                        step_reward, info_str = -0.5, "Wrong diagnosis (-0.5)"
                else:
                    self._wrong_action_count += 1
                    step_reward, info_str = -0.5, "Expected reply_to_customer (-0.5)"
            else:
                if action.tool_name == "close_ticket":
                    step_reward, info_str = 0.4, "Closed ticket (+0.4)"
                elif action.tool_name == "reply_to_customer":
                    content = str(action.tool_args.get("content", "")).lower()
                    if "v2.1" in content or "update client" in content:
                        step_reward, info_str = 0.6, "Late diagnosis (+0.6)"
                    else:
                        step_reward, info_str = -0.3, "Extra communication (-0.3)"
                elif action.tool_name == self._last_action:
                    step_reward, info_str = -0.3, "Repeated action (-0.3)"
                else:
                    step_reward, info_str = -0.5, f"{action.tool_name} (-0.5)"

        # Extra steps penalty
        min_steps = {"easy_ticket_1": 2, "medium_ticket_1": 2, "hard_ticket_1": 3}
        min_req = min_steps.get(task_id, 2)
        if step_count > min_req:
            step_reward -= 0.1 * (step_count - min_req)

        step_reward = max(-0.3, step_reward)
        self._total_reward += step_reward

        # Termination conditions
        if self._wrong_action_count >= 3 or step_count > 20:
            is_complete = True

        self._last_action = action.tool_name

        # Final normalization to [0.0, 1.0]
        norm = TASK_NORMALIZATION.get(task_id, 1.5)
        # We only pass back the total accumulated normalized reward so far
        final_score = max(0.0, min(1.0, self._total_reward / norm))

        # Update observation
        self._current_obs.done = is_complete
        self._current_obs.reward = round(final_score, 3)
        self._current_obs.metadata = {"info": info_str}

        return self._current_obs.model_copy(deep=True)

    @property
    def state(self) -> SupportState:
        """Return the current state snapshot."""
        return self._state.model_copy(deep=True)
