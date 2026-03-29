"""FastAPI server for OpenEnv Customer Support Ticket Environment."""
import logging
import os
from typing import Optional
from fastapi import FastAPI
from pydantic import BaseModel
from dotenv import load_dotenv
import uvicorn

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="OpenEnv — Customer Support Ticket Environment")

HF_TOKEN = os.getenv("HF_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
API_BASE_URL = os.getenv("API_BASE_URL")
MODEL_NAME = os.getenv("MODEL_NAME", "gpt-4.1-mini")

# Lazy-loaded environment components (initialized on first reset)
_env_state = {
    "environment": None,
    "task": None,
    "grader": None,
}


class ResetRequest(BaseModel):
    task_id: Optional[str] = "easy_ticket_1"


class StepRequest(BaseModel):
    tool_name: str
    tool_args: dict = {}


def _build_env(task_id: str):
    """Build an Environment for the given task_id."""
    from env.environment import Environment
    from tasks.easy import EasyTask
    from tasks.medium import MediumTask
    from tasks.hard import HardTask
    from graders.support_grader import SupportGrader

    task_map = {
        "easy_ticket_1": EasyTask,
        "medium_ticket_1": MediumTask,
        "hard_ticket_1": HardTask,
    }
    task_cls = task_map.get(task_id)
    if task_cls is None:
        raise ValueError(f"Unknown task_id: {task_id}. Choose from {list(task_map)}")

    grader = SupportGrader()
    task = task_cls()
    env = Environment(task, grader, max_steps=10)
    return env, grader


@app.get("/")
def root():
    """Health check — returns 200 to confirm the server is live."""
    return {
        "status": "running",
        "environment": "Customer Support OpenEnv",
        "version": "1.0",
    }


@app.get("/health")
def health():
    """Detailed health status (always returns 200)."""
    return {
        "status": "healthy",
        "hf_token_configured": bool(HF_TOKEN),
        "openai_api_configured": bool(OPENAI_API_KEY),
        "api_base_url": API_BASE_URL or "default",
        "model": MODEL_NAME,
    }


@app.get("/reset")
def reset_get():
    """GET reset — simple confirmation for HF Spaces ping validation."""
    return {
        "status": "reset_ready",
        "message": "Environment ready for new episode",
        "tasks_available": ["easy_ticket_1", "medium_ticket_1", "hard_ticket_1"],
    }


@app.post("/reset")
def reset_post(req: ResetRequest = ResetRequest()):
    """POST reset — initialize a new episode for the given task."""
    env, grader = _build_env(req.task_id)
    grader.reset_episode()
    obs = env.reset()

    _env_state["environment"] = env
    _env_state["grader"] = grader

    return obs.model_dump()


@app.post("/step")
def step(req: StepRequest):
    """Execute one action and return (observation, reward, done, info)."""
    from env.models import Action

    env = _env_state.get("environment")
    if env is None:
        return {"error": "Call /reset first to initialize an episode."}

    action = Action(tool_name=req.tool_name, tool_args=req.tool_args)
    obs, reward, done, info = env.step(action)

    return {
        "observation": obs.model_dump(),
        "reward": reward.model_dump(),
        "done": done,
        "info": info,
    }


@app.get("/state")
def state():
    """Return the current environment state."""
    env = _env_state.get("environment")
    if env is None:
        return {"error": "Call /reset first to initialize an episode."}
    return env.state().model_dump()


@app.get("/info")
def info():
    """Environment metadata."""
    return {
        "name": "OpenEnv — Customer Support Ticket Environment",
        "description": "Real-world customer support environment for AI agent evaluation",
        "tasks": ["easy_ticket_1", "medium_ticket_1", "hard_ticket_1"],
        "api_endpoints": ["/", "/health", "/reset", "/step", "/state", "/info"],
        "model": MODEL_NAME,
    }


if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info("Starting OpenEnv on port 7860")
    logger.info(f"  OpenAI API: {'configured' if OPENAI_API_KEY else 'not configured'}")
    logger.info(f"  HF Token:   {'configured' if HF_TOKEN else 'not configured'}")
    logger.info(f"  Model:      {MODEL_NAME}")
    logger.info("=" * 60)
    uvicorn.run(app, host="0.0.0.0", port=7860)
