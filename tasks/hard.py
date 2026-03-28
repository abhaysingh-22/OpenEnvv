"""Hard task implementations."""
from typing import Any, Dict
from env.models import Observation, Action
from .base_task import BaseTask


class HardTask(BaseTask):
    """
    Hard difficulty task: Technical Troubleshooting.
    
    Requires 3 steps minimum:
    1. Request logs to investigate
    2. Provide solution with explanation
    3. Optional: Close ticket
    """
    
    def __init__(self, task_id: str = "hard_ticket_1", title: str = "Technical Error", description: str = "API returning 500", initial_data: Dict[str, Any] = None):
        """Initialize a hard task."""
        super().__init__(task_id, title, description)
        self.completed = False
        self.history = []
        self.step_count = 0
        self.logs_requested = False
        self.solution_provided = False
        self.initial_obs = Observation(
            ticket_id="TKT-3001",
            user_name="Bob Jones",
            user_email="bob@example.com",
            subject="API is crashing",
            body="Every time I hit the /process endpoint, your API returns a 500 error. This is blocking our integration. Please fix ASAP.",
            history=[],
            system_data={
                "known_issues": {
                    "ERR-99": "Fix: Update client to v2.1",
                    "ERR-42": "Fix: Clear cache"
                },
                "error_code": "ERR-99"
            }
        )
    
    def reset(self) -> Observation:
        """Reset the task to initial state."""
        self.completed = False
        self.history = []
        self.step_count = 0
        self.logs_requested = False
        self.solution_provided = False
        self.state = self.initial_obs.model_copy(deep=True)
        return self.state
    
    def step(self, action: Action) -> Observation:
        """
        Execute one step of the task.
        
        Step 1: Should request logs
        Step 2: Should provide solution
        Step 3+: Optional closure
        """
        if self.state is None:
            self.reset()
        
        self.step_count += 1
        self.history.append({"agent": action.model_dump()})
        
        if self.step_count == 1:
            # First step: should request logs
            if action.tool_name == "request_logs":
                self.logs_requested = True
                self.history.append({
                    "system": "Logs Retrieved:\n[ERROR] Connection refused at 2026-03-27 14:32:15\nCode: ERR-99\nClient Version: v2.0.5"
                })
            elif action.tool_name == "reply_to_customer":
                # Responding without investigation (suboptimal)
                content = str(action.tool_args.get("content", "")).lower()
                if "update client to v2.1" in content or "v2.1" in content:
                    self.solution_provided = True
                    self.history.append({"user": "Got it! Let me update my client."})
                else:
                    self.history.append({"user": "That doesn't make sense. Can you be more specific?"})
            else:
                self.history.append({"system": f"Acknowledged action: {action.tool_name}"})
        
        elif self.step_count >= 2:
            # Step 2+: should provide solution
            if action.tool_name == "reply_to_customer":
                content = str(action.tool_args.get("content", "")).lower()
                if "update client to v2.1" in content or "v2.1" in content:
                    self.solution_provided = True
                    if self.logs_requested:
                        self.history.append({
                            "user": "Perfect! That fixed it. The /process endpoint is working now. Thank you!"
                        })
                    else:
                        self.history.append({
                            "user": "Let me try that... actually, it's working now but I'm not sure why your suggestion helped."
                        })
                    # Auto-complete if solution provided
                    if self.step_count >= 2:
                        self.completed = True
                else:
                    self.history.append({"user": "I tried that but it didn't work. Still getting the 500 error."})
            elif action.tool_name == "request_logs":
                if not self.logs_requested:
                    self.logs_requested = True
                    self.history.append({
                        "system": "Logs Retrieved:\n[ERROR] Connection refused.\nCode: ERR-99"
                    })
                else:
                    self.history.append({"system": "Logs already retrieved."})
            elif action.tool_name == "close_ticket":
                if self.solution_provided:
                    self.completed = True
                    self.history.append({"system": "Ticket closed successfully."})
                else:
                    self.history.append({"system": "Cannot close - solution not yet provided."})
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
