FROM python:3.10-slim

WORKDIR /app
 
# Optimize Python and pip behavior in containers
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# ────────────────────────────────────────────────────────────────────
# CACHE-BUSTER: Forces fresh build on HuggingFace Spaces
# Updated: 2026-04-12 FINAL - Comprehensive reward safety pipeline
# - Pre-clamp: (0.0005, 0.9994) prevents rounding to edges
# - Post-clamp: (0.001, 0.999) defense in depth
# - Pydantic validator: ensures (0, 1) strictly at API level
# - Assertion: runtime check every reward calculation
# ────────────────────────────────────────────────────────────────────
RUN echo "Final comprehensive safety pipeline:" && \
    echo "  ✓ Math proven safe: round(0.0005, 3)=0.001, round(0.9994, 3)=0.999" && \
    echo "  ✓ No reward can reach 0.0 or 1.0 mathematically" && \
    echo "  ✓ Pydantic validator enforces (0, 1) strictly" && \
    echo "  ✓ Runtime assertions verify every step"

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
