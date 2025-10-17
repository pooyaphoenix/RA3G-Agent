# Use a lightweight Python base image
FROM python:3.11-slim

# Set environment variables to avoid interactive prompts and improve pip reliability
ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DEFAULT_TIMEOUT=300 \
    PIP_RETRIES=10

# Install system dependencies (important for faiss-cpu and other ML libs)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    g++ \
    wget \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy dependency file first to leverage Docker layer caching
COPY requirements.txt .

# Upgrade pip and install Python dependencies with increased timeout
RUN pip install --upgrade pip \
    && pip install --default-timeout=300 -r requirements.txt

# Copy project files
COPY . .

# Expose port if needed
EXPOSE 8010

# Run your app (example for FastAPI)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8010"]
