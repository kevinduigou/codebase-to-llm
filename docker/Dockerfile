# Use Python 3.12 slim image as base
FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/src

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install uv for faster Python package management
RUN pip install uv

# Copy source code and dependency files
COPY ../src ./src
COPY ../pyproject.toml ../uv.lock ./

# Install Python dependencies
RUN uv sync --frozen --dev

# Copy and make entrypoint script executable
COPY docker/entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# Create directories for data persistence
RUN mkdir -p /app/data

# Expose port
EXPOSE 8000

# Set environment variables for the application
ENV DATABASE_URL=sqlite:///./data/users.db

# Use entrypoint script
ENTRYPOINT ["/app/entrypoint.sh"]
