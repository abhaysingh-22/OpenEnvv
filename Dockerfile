FROM python:3.10-slim

WORKDIR /app

# Environment variables for Python optimization and pip
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements, install them, and then immediately UNINSTALL heavy unused packages 
# in the SAME layer to drastically reduce the final image size (removes ~800MB of UI/audio libs)
COPY requirements.txt pyproject.toml ./
RUN pip install --no-cache-dir -r requirements.txt && \
    pip uninstall -y gradio gradio-client hf-gradio ffmpy numpy pandas pydub scipy matplotlib soundfile || true

# Copy application source code
COPY . .

# Install the Support Environment package properly and clear cache/bytecode
RUN pip install --no-cache-dir --no-deps -e . && \
    find / -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true

# Create non-root user for security
RUN useradd --create-home appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 7860

# Health check matching OpenEnv standard
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:7860/health || exit 1

# Start the OpenEnv server via uvicorn wrapper
CMD ["uvicorn", "server.app:app", "--host", "0.0.0.0", "--port", "7860", "--log-level", "info"]
