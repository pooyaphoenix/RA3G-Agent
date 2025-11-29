# Use a lightweight Python base image
FROM python:3.11-slim

# Environment setup
ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DEFAULT_TIMEOUT=300 \
    PIP_RETRIES=10

# Install system dependencies (needed for faiss-cpu, streamlit, etc.)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    g++ \
    wget \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy dependency file first (for Docker cache)
COPY requirements.txt .

# Install dependencies (split into separate RUN for better caching)
# Install heavy ML dependencies first (these change less frequently)
RUN pip install --upgrade pip && \
    pip install --default-timeout=300 torch torchvision --index-url https://download.pytorch.org/whl/cpu

# Install remaining dependencies
RUN pip install --default-timeout=300 -r requirements.txt

# Copy all project files
COPY . .

# Expose ports
EXPOSE 8010 8501

# Default command
CMD ["python", "ra3g.py", "--api-port", "8010", "--ui-port", "8501"]
