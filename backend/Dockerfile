# Multi-stage Dockerfile for Digital FTE Backend
# Optimized for production with minimal image size

# Stage 1: Builder
FROM python:3.11-slim as builder

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONDONTWRITEPYC=1 \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Upgrade pip and install build requirements
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -U pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY backend/src /app/src
COPY backend/alembic /app/alembic
COPY backend/pyproject.toml /app/

# Stage 2: Production Image
FROM python:3.11-slim

# Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Set working directory
WORKDIR /app

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv

# Copy application code
COPY --from=builder /app /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONDONTWRITEPYC=1 \
    PATH="/opt/venv/bin:$PATH" \
    APP_HOME=/app \
    PYTHONPATH="/app/src:$PYTHONPATH"

# Install runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Create directories
RUN mkdir -p /app/logs /app/tmp && \
    chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health/live || exit 1

# Expose port
EXPOSE 8000

# Run application using Gunicorn for production process management
CMD ["gunicorn", "src.main:app", \\
     "--workers", "4", \\
     "--worker-class", "uvicorn.workers.UvicornWorker", \\
     "--bind", "0.0.0.0:8000", \\
     "--access-logfile", "-", \\
     "--error-logfile", "-", \\
     "--log-level", "info", \\
     "--timeout", "120"]
