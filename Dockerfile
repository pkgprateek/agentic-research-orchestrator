# Market Intelligence Agent - Dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY src/ ./src/
COPY scripts/ ./scripts/
COPY conftest.py .

# Create necessary directories
RUN mkdir -p data logs

# Expose ports
EXPOSE 8000 7860

# Default command runs both API and UI
CMD uvicorn src.api.main:app --host 0.0.0.0 --port 8000 & python src/ui/app.py
