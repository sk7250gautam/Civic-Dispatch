# ==============================================================================
# CIVIC DISPATCH — Root Dockerfile for Render / Cloud Deployments
# Dynamically binds to $PORT provided by Render, Heroku, or Cloud Run
# ==============================================================================
FROM python:3.13-slim-bookworm

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    FLASK_APP=run.py

WORKDIR /app

# Install system dependencies for Pillow and PostgreSQL
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies from backend/requirements.txt
COPY backend/requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy backend source code to /app
COPY backend/ .

# Ensure uploads folder exists and set permissions
RUN mkdir -p /app/uploads && \
    groupadd -r civic && useradd -r -g civic -d /app civicuser && \
    chown -R civicuser:civic /app

USER civicuser

EXPOSE 5000

# Auto-seed database tables and start Gunicorn dynamically on Render's $PORT
CMD ["sh", "-c", "flask seed-db && gunicorn --bind 0.0.0.0:${PORT:-5000} --workers 2 --threads 2 --timeout 60 run:app"]
