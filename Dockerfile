# ==============================================
# Behavioral Health Platform - Python API
# Multi-stage production Dockerfile
# ==============================================

FROM python:3.11-slim AS base

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        curl \
        build-essential \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd --gid 1000 appuser && \
    useradd --uid 1000 --gid appuser --shell /bin/bash --create-home appuser

WORKDIR /app

# --------------- Dependencies Stage ---------------
FROM base AS dependencies

# Copy requirements first for better layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -i https://pypi.tuna.tsinghua.edu.cn/simple --trusted-host pypi.tuna.tsinghua.edu.cn -r requirements.txt

# --------------- Production Stage ---------------
FROM base AS production

# Copy installed packages from dependencies stage
COPY --from=dependencies /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=dependencies /usr/local/bin /usr/local/bin

# Copy application source code
COPY api/ ./api/
COPY core/ ./core/
COPY services/ ./services/
COPY configs/ ./configs/
COPY models/ ./models/
COPY agents/ ./agents/
COPY protocols/ ./protocols/
COPY integrations/ ./integrations/
COPY disclosure/ ./disclosure/
COPY quality/ ./quality/
COPY alembic/ ./alembic/
COPY data/ ./data/
COPY config.yaml ./
COPY alembic.ini ./
COPY main.py ./
COPY cli.py ./

# Create directories for runtime data
RUN mkdir -p /app/logs /app/data && \
    chown -R appuser:appuser /app

# Expose API ports
EXPOSE 8000 8001 8002

# Switch to non-root user
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run the API server
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4", "--log-level", "info"]
