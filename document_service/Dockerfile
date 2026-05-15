FROM python:3.11-slim

WORKDIR /app

# Install system dependencies including Tesseract for OCR
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    tesseract-ocr \
    tesseract-ocr-eng \
    libtesseract-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY config.py .
COPY document_service/ ./document_service/

# Create directories for file uploads
RUN mkdir -p /app/uploads /app/temp_files && chown -R 1000:1000 /app/uploads /app/temp_files

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8003

# Run the application
CMD ["uvicorn", "document_service.main:app", "--host", "0.0.0.0", "--port", "8003"]
