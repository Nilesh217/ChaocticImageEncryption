# backend/Dockerfile
FROM python:3.11-slim

# Prevent Python from generating .pyc files and enable unbuffered standard I/O logging
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Install system-level dependencies required by scientific computing & image libraries
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libgl1 \
    libglib2.0-0 \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy dependency requirements first to leverage Docker layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend application source files
COPY . .

# Default port configuration (dynamically overridden by cloud providers like Render / Cloud Run)
ENV PORT=8000
EXPOSE 8000

# Automated healthcheck for container orchestration and uptime monitoring
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:${PORT}/docs || exit 1

# Launch Uvicorn bound to 0.0.0.0 using dynamic shell variable expansion
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT}"]
