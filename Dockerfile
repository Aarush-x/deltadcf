FROM python:3.11-slim

# Install system dependencies needed for PyMuPDF (fitz) and compilation
RUN apt-get update && apt-get install -y \
    build-essential \
    libmupdf-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

# Expose port and start FastAPI server
EXPOSE 8000
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]
