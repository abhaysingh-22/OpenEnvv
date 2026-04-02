import os
import uvicorn
from openenv.core.env_server import create_app

from support_env.models import SupportAction, SupportObservation
from support_env.server.support_environment import SupportEnvironment

app = create_app(
    SupportEnvironment,
    SupportAction,
    SupportObservation,
    env_name="support_env"
)

@app.get("/")
def read_root():
    return {"message": "Welcome to the OpenEnv Customer Support API! Connect your agents to the endpoints or append /docs to this URL for the UI."}

@app.get("/health")
def health_check():
    """Health check endpoint for Hugging Face Spaces and container orchestration."""
    return {"status": "ok"}

if __name__ == "__main__":
    port = int(os.getenv("PORT", 7860))
    uvicorn.run("support_env.server.app:app", host="0.0.0.0", port=port, reload=True)
