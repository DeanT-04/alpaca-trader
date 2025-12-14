FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency files
COPY pyproject.toml README.md ./

# Install python dependencies
RUN pip install --no-cache-dir .

# Copy source code
COPY src src/

# Create non-root user
RUN useradd -m appuser && chown -R appuser /app
USER appuser

ENTRYPOINT ["alpaca-trader"]
