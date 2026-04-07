FROM python:3.10-slim

WORKDIR /app
 
# Optimize Python and pip behavior in containers
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install Python dependencies, then strip heavy unused transitive deps in SAME layer
# openenv-core pulls gradio/numpy/etc. for rich envs — we only need the HTTP server core
COPY requirements.txt pyproject.toml ./
RUN pip install --no-cache-dir -r requirements.txt && \
    pip uninstall -y \
        gradio gradio-client hf-gradio \
        ffmpy numpy pandas pydub scipy matplotlib soundfile pillow \
        aiofiles ruff semantic-version tomlkit \
        2>/dev/null || true && \
    find /usr/local/lib/python3.10 -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null; \
    find /usr/local/lib/python3.10 -type d -name tests -prune -exec rm -rf {} + 2>/dev/null; \
    find /usr/local/lib/python3.10 -name "*.pyc" -delete 2>/dev/null; \
    rm -rf /tmp/* /root/.cache; true

# Copy application source
COPY . .

# Install project package (no-deps: all deps already installed above)
RUN pip install --no-cache-dir --no-deps . && \
    find /app -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true

# Security: non-root user (required for HF Spaces)
RUN useradd --create-home appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 7860

# Healthcheck using Python stdlib (avoids installing curl / apt-get entirely)
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:7860/health')" || exit 1

# Start the OpenEnv server (matches openenv.yaml app path)
CMD ["uvicorn", "support_env.server.app:app", "--host", "0.0.0.0", "--port", "7860", "--log-level", "info"]
