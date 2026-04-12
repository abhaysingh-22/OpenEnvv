"""Pydantic models for the Support Environment."""
from typing import Any, Dict, List
from openenv.core.env_server import Action, Observation, State
from pydantic import Field, field_validator


class SupportAction(Action):
    """Agent action — selects a tool and provides arguments."""
    tool_name: str = Field(description="One of: reply_to_customer, issue_refund, send_password_reset, request_logs, close_ticket")
    tool_args: Dict[str, Any] = Field(default_factory=dict)


class SupportObservation(Observation):
    """Observation returned by the environment at each step."""
    ticket_id: str
    user_name: str
    user_email: str
    subject: str
    body: str
    history: List[Dict[str, Any]] = Field(default_factory=list)
    system_data: Dict[str, Any] = Field(default_factory=dict)
    
    @field_validator('reward')
    @classmethod
    def validate_reward_range(cls, v):
        """Ensure reward is strictly between 0 and 1 (exclusive)."""
        if v is None:
            v = 0.5  # Default to neutral value
        
        # Check exact equality first (catches 0.0 and 1.0)
        if v == 0.0 or v == 1.0:
            raise ValueError(f"Reward must be strictly between 0 and 1 (exclusive), got {v}")
        
        # Check range
        if v <= 0.0 or v >= 1.0:
            raise ValueError(f"Reward must be strictly between 0 and 1 (exclusive), got {v}")
        
        return v


class SupportState(State):
    """Full environment state snapshot."""
    task_id: str
    # State has a `step_count` field by default in openenv-core
    # Observation also has `done` and `reward` inside openenv-core


