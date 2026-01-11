# Dockerfile - Development Environment
# YuKyuDATA FastAPI Application
#
# Usage:
#   docker build -t yukyu-dev .
#   docker run -p 8000:8000 yukyu-dev
#
# For development with hot-reload, use docker-compose.dev.yml

FROM python:3.11-slim

LABEL maintainer="YuKyuDATA Team"
LABEL version="1.0-dev"
LABEL description="YuKyuDATA Development Environment"

# ============================================
# SYSTEM DEPENDENCIES
# ============================================
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# ============================================
# WORKING DIRECTORY
# ============================================
WORKDIR /app

# ============================================
# PYTHON DEPENDENCIES
# ============================================
# Copy requirements first for better layer caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir \
    fastapi \
    uvicorn[standard] \
    openpyxl \
    python-multipart \
    pydantic \
    PyJWT \
    python-dotenv \
    XlsxWriter \
    pytest \
    pytest-cov \
    httpx \
    requests

# Install additional dependencies from requirements.txt if exists
RUN if [ -f requirements.txt ]; then pip install --no-cache-dir -r requirements.txt; fi

# ============================================
# COPY APPLICATION CODE
# ============================================
# Note: In development, we mount volumes for hot-reload
# These copies are for standalone container usage
COPY main.py .
COPY database.py .
COPY excel_service.py .
COPY fiscal_year.py .
COPY templates/ ./templates/
COPY static/ ./static/

# Copy optional files if they exist
COPY config.py . 2>/dev/null || true
COPY logger.py . 2>/dev/null || true
COPY excel_export.py . 2>/dev/null || true

# ============================================
# ENVIRONMENT VARIABLES
# ============================================
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    APP_ENV=development \
    DEBUG=true

# ============================================
# CREATE DATA DIRECTORIES
# ============================================
RUN mkdir -p /app/data /app/logs /app/backups && \
    chmod 755 /app/data /app/logs /app/backups

# ============================================
# HEALTHCHECK
# ============================================
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/db-status || exit 1

# ============================================
# EXPOSE PORT
# ============================================
EXPOSE 8000

# ============================================
# DEFAULT COMMAND (Development with reload)
# ============================================
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
