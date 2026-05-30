FROM python:3.12-slim

WORKDIR /app

# System dependencies for PDF parsing
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app/ ./app/
COPY vector_store_mock.json ./vector_store_mock.json

# Never run as root
RUN useradd -m appuser
USER appuser

EXPOSE 8000

# Production start command
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
