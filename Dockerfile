# Use Python 3.11 slim image as base
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive

# Set work directory
WORKDIR /app

# Install system dependencies including those needed for playwright
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    wget \
    curl \
    # Playwright browser dependencies
    libnss3 \
    libnspr4 \
    libatk-bridge2.0-0 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    libgbm1 \
    libxss1 \
    libasound2 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY requirements.txt .

# Install Python dependencies and playwright browsers
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    playwright install chromium --with-deps

# Copy application code
COPY . .

# Create data directories with proper permissions
RUN mkdir -p /app/data /app/sharesansarTSP /app/logs && \
    chmod 755 /app/data /app/sharesansarTSP /app/logs

# Create a non-root user for security
RUN adduser --disabled-password --gecos '' appuser && \
    chown -R appuser:appuser /app

USER appuser

# Expose volumes for data persistence
VOLUME ["/app/data", "/app/sharesansarTSP", "/app/logs"]

# Set default command to run the auto historic scraper (option 1 with auto-confirm)
CMD ["python", "auto_historic_scraper.py"]
