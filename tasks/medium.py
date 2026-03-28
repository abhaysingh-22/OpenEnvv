"""Medium task implementations."""
from typing import Any, Dict
from env.models import Observation, Action
from .base_task import BaseTask


class MediumTask(BaseTask):
    """
    Medium difficulty task: Refund Request with Policy Check.
    
    Requires 2-3 steps minimum:
    1. Check policy or respond
    2. Provide policy-aware response
    3. Optional: Close ticket
    """
    
    def __init__(self, task_id: str = "medium_ticket_1", title: str = "Refund Request", description: str = "Check refund policy", initial_data: Dict[str, Any] = None):
        """Initialize a medium task."""
        super().__init__(task_id, title, description)
        self.completed = False
        self.history = []
        self.step_count = 0
        self.policy_checked = False
        self.policy_response_given = False
        self.initial_obs = Observation(
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
                "refund_policy_days": 30
            }
        )
    
    def reset(self) -> Observation:
        """Reset the task to initial state."""
        self.completed = False
        self.history = []
        self.step_count = 0
        self.policy_checked = False
        self.policy_response_given = False
        self.state = self.initial_obs.model_copy(deep=True)
        return self.state
    
    def step(self, action: Action) -> Observation:
        """
        Execute one step of the task.
        
        Step 1: Can check policy or respond
        Step 2+: Should provide policy-aware response
        """
        if self.state is None:
            self.reset()
        
        self.step_count += 1
        self.history.append({"agent": action.model_dump()})
        
        if self.step_count == 1:
            # First step: can check policy or respond
            if action.tool_name == "request_logs":
                # Checking policy/system data
                self.policy_checked = True
                self.history.append({"system": "Policy Check: 30-day refund limit. Purchase was 45 days ago. DENY refund."})
            elif action.tool_name == "reply_to_customer":
                content = str(action.tool_args.get("content", "")).lower()
                if any(kw in content for kw in ["deny", "policy", "cannot", "30"]):
                    self.policy_response_given = True
                    self.history.append({"user": "I understand, thank you for checking."})
                    self.completed = True
                else:
                    self.history.append({"user": "Does that mean I get a refund?"})
            elif action.tool_name == "issue_refund":
                self.history.append({"system": "ERROR: Refund issued outside policy window!"})
            else:
                self.history.append({"system": f"Acknowledged action: {action.tool_name}"})
        
        elif self.step_count >= 2:
            # Step 2+: should provide clear policy-based response
            if action.tool_name == "reply_to_customer":
                content = str(action.tool_args.get("content", "")).lower()
                if any(kw in content for kw in ["deny", "policy", "cannot", "30"]):
                    self.policy_response_given = True
                    self.history.append({"user": "I understand, thank you for checking."})
                    self.completed = True
                else:
                    self.history.append({"user": "I'm still confused about the refund."})
            elif action.tool_name == "issue_refund":
                self.history.append({"system": "ERROR: Refund policy violation!"})
            elif action.tool_name == "close_ticket":
                if self.policy_response_given:
                    self.completed = True
                    self.history.append({"system": "Ticket closed."})
                else:
                    self.history.append({"system": "Cannot close - issue not fully addressed."})
            elif action.tool_name == "request_logs":
                # Already checked
                if not self.policy_checked:
                    self.policy_checked = True
                    self.history.append({"system": "Policy Check: 30-day refund limit. DENY refund."})
                else:
                    self.history.append({"system": "Policy already checked."})
            else:
                self.history.append({"system": f"Acknowledged action: {action.tool_name}"})
        
        # Update history in state
        if not hasattr(self.state, 'history'):
            self.state.history = []
        self.state.history.extend(self.history[-2:])
        
        return self.state
    
    def is_complete(self) -> bool:
        """Check if the task has been completed successfully."""
        return self.completed
