# Base image
FROM python:3.10-slim

# Install system dependencies (ffmpeg included)
RUN apt-get update && apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Set workdir
WORKDIR /app

# Copy requirements
COPY requirements.txt .

# Install python deps
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Run with gunicorn
CMD ["gunicorn", "-w", "2", "-k", "gthread", "--threads", "8", "--timeout", "180", "app:app"]
