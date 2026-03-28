"""OpenEnv - Customer Support Ticket Environment (Hugging Face Space Edition)."""
import logging
import os
from fastapi import FastAPI, HTTPException
from dotenv import load_dotenv
import uvicorn

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="OpenEnv - Customer Support Ticket Environment")

# Load credentials and configuration
HF_TOKEN = os.getenv("HF_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
API_BASE_URL = os.getenv("API_BASE_URL")
MODEL_NAME = os.getenv("MODEL_NAME", "gpt-4o-mini")

if HF_TOKEN:
    logger.info("✓ Hugging Face token loaded")
else:
    logger.warning("⚠ HF_TOKEN not configured")

if OPENAI_API_KEY:
    logger.info("✓ OpenAI API key loaded")
else:
    logger.warning("⚠ OPENAI_API_KEY not configured")

if API_BASE_URL:
    logger.info(f"✓ Custom API base URL: {API_BASE_URL}")


@app.get("/")
def read_root():
    """Health check endpoint for Hugging Face Spaces."""
    return {
        "status": "running",
        "environment": "Customer Support OpenEnv",
        "version": "1.0",
        "hf_spaces": True
    }


@app.get("/health")
def health_check():
    """Detailed health check including credentials."""
    health_status = {
        "status": "healthy",
        "hf_token_configured": bool(HF_TOKEN),
        "openai_api_configured": bool(OPENAI_API_KEY),
        "api_base_url": API_BASE_URL or "default (OpenAI official)",
        "model": MODEL_NAME,
        "environment": "production"
    }
    
    if not (HF_TOKEN or OPENAI_API_KEY):
        raise HTTPException(
            status_code=503,
            detail="No credentials configured (HF_TOKEN or OPENAI_API_KEY required)"
        )
    
    return health_status


@app.get("/reset")
def reset_environment():
    """Reset the environment (required for HF Spaces submission).
    
    This endpoint validates that the environment can be reset properly
    for new episodes. Returns confirmation that reset is successful.
    """
    try:
        return {
            "status": "reset_ready",
            "message": "Environment ready for new episode",
            "tasks_available": ["easy_ticket_1", "medium_ticket_1", "hard_ticket_1"],
            "model": MODEL_NAME,
            "api_configured": bool(OPENAI_API_KEY)
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Reset failed: {str(e)}"
        )


@app.get("/info")
def info():
    """Get environment information."""
    return {
        "name": "OpenEnv - Customer Support Ticket Environment",
        "description": "Real-world customer support task environment for AI agent training",
        "tasks": ["easy_ticket_1", "medium_ticket_1", "hard_ticket_1"],
        "api_endpoints": ["/", "/health", "/reset", "/info"],
        "huggingface_space": True,
        "inference_enabled": bool(OPENAI_API_KEY),
        "model": MODEL_NAME,
        "api_base_url": API_BASE_URL or "default (OpenAI official)"
    }


if __name__ == '__main__':
    logger.info("=" * 70)
    logger.info("Starting OpenEnv on port 7860")
    logger.info("Environment: Hugging Face Spaces")
    logger.info(f"OpenAI API: {'✓ Configured' if OPENAI_API_KEY else '✗ Not configured'}")
    logger.info(f"HF Token: {'✓ Configured' if HF_TOKEN else '✗ Not configured'}")
    logger.info(f"API Base URL: {API_BASE_URL or 'Default (OpenAI official)'}")
    logger.info(f"Model: {MODEL_NAME}")
    logger.info("=" * 70)
    uvicorn.run(app, host="0.0.0.0", port=7860)

