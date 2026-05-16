FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements-lite.txt .
RUN pip install --no-cache-dir -r requirements-lite.txt

# Copy application code
COPY config.py .
COPY rag_service/ ./rag_service/

# Create directories for vector database
RUN mkdir -p /app/chroma_db && chown -R 1000:1000 /app/chroma_db

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8002

# Run the application
CMD ["uvicorn", "rag_service.main:app", "--host", "0.0.0.0", "--port", "8002"]
