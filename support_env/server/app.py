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

if __name__ == "__main__":
    port = int(os.getenv("PORT", 7860))
    uvicorn.run("support_env.server.app:app", host="0.0.0.0", port=port, reload=True)
