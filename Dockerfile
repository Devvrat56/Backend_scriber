# Use Python 3.10-slim for a smaller base and better AI wheel support
FROM python:3.10-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV PORT 8080

# Install system dependencies (Heavy cleanup to save space)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    g++ \
    libgl1 \
    libglib2.0-0 \
    ffmpeg \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# 1. Install CPU-only Torch and pin Numpy < 2.0.0 to prevent version conflicts
RUN pip install --no-cache-dir "numpy<2.0.0" torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu

# 2. Install remaining dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files (Filtered by .dockerignore)
COPY . .

# Create necessary folders
RUN mkdir -p uploads

# Expose port
EXPOSE $PORT

# Start the application
CMD uvicorn main:app --host 0.0.0.0 --port $PORT
