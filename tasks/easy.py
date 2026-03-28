"""Easy task implementations."""
from typing import Any, Dict
from env.models import Observation, Action
from .base_task import BaseTask


class EasyTask(BaseTask):
    """
    Easy difficulty task: Password Reset.
    
    Requires 2 steps minimum:
    1. Send password reset link
    2. Verify/Close ticket
    """
    
    def __init__(self, task_id: str = "easy_ticket_1", title: str = "Password Reset Request", description: str = "User forgot password", initial_data: Dict[str, Any] = None):
        """Initialize an easy task."""
        super().__init__(task_id, title, description)
        self.completed = False
        self.history = []
        self.reset_sent = False
        self.step_count = 0
        self.initial_obs = Observation(
            ticket_id="TKT-1001",
            user_name="John Doe",
            user_email="john@example.com",
            subject="Cannot login, forgot password",
            body="Hi support, I forgot my password and cannot access my account. Please help.",
            history=[],
            system_data={"account_status": "active"}
        )
    
    def reset(self) -> Observation:
        """Reset the task to initial state."""
        self.completed = False
        self.history = []
        self.reset_sent = False
        self.step_count = 0
        self.state = self.initial_obs.model_copy(deep=True)
        return self.state
    
    def step(self, action: Action) -> Observation:
        """
        Execute one step of the task.
        
        Step 1: Should send password reset
        Step 2+: Should close or verify
        """
        if self.state is None:
            self.reset()
        
        self.step_count += 1
        self.history.append({"agent": action.model_dump()})
        
        if self.step_count == 1:
            # First step: expect password reset
            if action.tool_name == "send_password_reset" and action.tool_args.get("email") == "john@example.com":
                self.reset_sent = True
                self.history.append({"user": "Thanks, I received the password reset link. Let me try logging in."})
            elif action.tool_name == "reply_to_customer":
                self.history.append({"user": "I just need a password reset link, please."})
            elif action.tool_name == "close_ticket":
                self.history.append({"system": "Cannot close without addressing issue."})
            else:
                self.history.append({"system": f"Acknowledged action: {action.tool_name}"})
        
        elif self.step_count >= 2:
            # Step 2+: expect closure or verification
            if action.tool_name == "close_ticket":
                if self.reset_sent:
                    self.completed = True
                    self.history.append({"system": "Ticket closed successfully."})
                else:
                    self.history.append({"system": "Cannot close - issue not resolved."})
            elif action.tool_name == "send_password_reset" and self.reset_sent:
                self.history.append({"system": "Password reset already sent."})
            elif action.tool_name == "reply_to_customer":
                self.history.append({"user": "Did you verify the reset link worked?"})
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
