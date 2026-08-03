# Use a slim Python 3.12 image
FROM python:3.12-slim

# Install system dependencies (git is required because we install evoid from a git repository)
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Set working directory
WORKDIR /app

# Enable bytecode compilation and python-compiled environment
ENV UV_COMPILE_BYTECODE=1
ENV PATH="/app/.venv/bin:$PATH"

# Copy package config files
COPY pyproject.toml uv.lock ./

# Install dependencies using uv (not the project itself first, to leverage cache)
RUN uv sync --frozen --no-install-project --no-dev

# Copy the rest of the application code
COPY . .

# Sync the project itself
RUN uv sync --frozen --no-dev

# By default, use python
CMD ["python"]
