FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Set environment variables to prevent Python from writing pyc files and buffering output
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies required for building Python packages
# Including build-essential for torch compilation and other packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
# Using --no-cache-dir flag already set in PIP_NO_CACHE_DIR
RUN pip install -r requirements.txt

# Copy application code
COPY . .

# Expose port for Hugging Face Spaces
EXPOSE 7860

# Health check for container orchestration
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:7860/health || exit 1

# Run the application
CMD ["python", "app.py"]
