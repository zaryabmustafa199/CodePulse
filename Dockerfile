# Multi-language Dual-Runtime Production Dockerfile for CodePulse Backend
FROM python:3.13-slim

# Install system utilities, Node.js 20 LTS, and npm
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    git \
    build-essential \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Install Python dependencies & static linter tools (Ruff, Bandit, Pip-Audit)
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir ruff bandit pip-audit

# Install Node.js global linter tools (ESLint)
RUN npm install -g eslint

# Copy application source code and configuration
COPY src/ ./src/

# Expose Uvicorn default port
EXPOSE 8000

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PORT=8000

# Start production ASGI server with Uvicorn
CMD ["uvicorn", "src.backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
