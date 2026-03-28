"""Main application entry point for OpenEnv - Hugging Face Space FastAPI App."""
import logging
from fastapi import FastAPI
import uvicorn

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="OpenEnv - Customer Support Ticket Environment")


@app.get("/")
def read_root():
    """Health check for Hugging Face space."""
    return {"status": "running", "environment": "Customer Support OpenEnv"}


if __name__ == '__main__':
    logger.info("Starting OpenEnv application on port 7860")
    uvicorn.run(app, host="0.0.0.0", port=7860)

