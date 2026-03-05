# Use official Python image
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y 
    build-essential 
    libpq-dev 
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY pyproject.toml .
RUN pip install --no-cache-dir .

# Copy production code
COPY production/ ./production/

# Set Python path
ENV PYTHONPATH=/app

# Default command (overridden in deployments)
CMD ["uvicorn", "production.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
