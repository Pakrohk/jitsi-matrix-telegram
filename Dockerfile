# Multi-stage build for matrix-jitsi-bot
FROM python:3.12-slim as builder

WORKDIR /app

# Install dependencies
COPY pyproject.toml ./
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir hatch

# Copy source
COPY . .

# Build wheel
RUN pip install --no-cache-dir --prefix=/install .

# Production stage
FROM python:3.12-slim

WORKDIR /app

# Copy installed packages
COPY --from=builder /install /usr/local

# Copy source code
COPY . .

# Expose ports
EXPOSE 8000 8001 8002 8003

# Default command
CMD ["python", "-m", "services.gateway.main"]
