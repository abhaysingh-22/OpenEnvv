"""Client to interact with the SupportEnv via HTTP/WebSocket."""
from typing import Any, Dict

from openenv.core.client_types import StepResult
from openenv.core.env_client import EnvClient

from .models import SupportAction, SupportObservation, SupportState


class SupportEnv(EnvClient[SupportAction, SupportObservation, SupportState]):
    """Client for the Customer Support Environment."""

    def _step_payload(self, action: SupportAction) -> dict:
        """Serialize action to raw dict."""
        return {
            "tool_name": action.tool_name,
            "tool_args": action.tool_args,
        }

    def _parse_result(self, payload: dict) -> StepResult[SupportObservation]:
        """Deserialize step response."""
        obs_dict = payload.get("observation", {})
        obs = SupportObservation(**obs_dict)
        return StepResult(
            observation=obs,
            reward=payload.get("reward"),
            done=payload.get("done", False),
        )

    def _parse_state(self, payload: dict) -> SupportState:
        """Deserialize state payload."""
        return SupportState(**payload)

    def _parse_observation(self, payload: dict) -> SupportObservation:
        """Deserialize initial observation from reset."""
        return SupportObservation(**payload)


