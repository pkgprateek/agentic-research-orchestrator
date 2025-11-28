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
# Install uv and dependencies
RUN pip install uv && \
    uv pip install --system --no-cache-dir -r requirements.txt

# Copy application
COPY src/ ./src/
COPY scripts/ ./scripts/
COPY conftest.py .

# Create necessary directories
RUN mkdir -p data logs

# Set python path
ENV PYTHONPATH=/app

# Expose ports
EXPOSE 8000 7860

# Default command runs both API and UI
CMD ["python", "src/ui/app.py"]
