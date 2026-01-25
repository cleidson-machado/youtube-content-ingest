# Dockerfile for YouTube Content Ingest Pipeline
# Base image: Python 3.11 slim for optimal size/functionality balance
FROM python:3.11-slim

# Metadata
LABEL maintainer="devops@aguide-ptbr.com.br"
LABEL description="YouTube Content Ingest Pipeline - Automated video discovery and API integration"
LABEL version="1.0.0"

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    TZ=America/Sao_Paulo

# Install system dependencies (if needed)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    tzdata \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user for security
RUN groupadd -r appuser && \
    useradd -r -g appuser -u 1001 appuser

# Set working directory
WORKDIR /app

# Copy requirements first (for Docker cache optimization)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY youtube_ingest/ ./youtube_ingest/
COPY main.py .

# Change ownership to non-root user
RUN chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Health check (optional - checks if Python can import the module)
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import youtube_ingest" || exit 1

# Default command (can be overridden in docker-compose or Jenkins)
CMD ["python", "main.py"]
