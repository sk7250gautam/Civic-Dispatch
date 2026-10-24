# ==============================================================================
# CIVIC DISPATCH — Production Backend Container
# Python 3.13 Slim with Non-Root Security & Healthcheck
# ==============================================================================
FROM python:3.13-slim-bookworm

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=5000 \
    FLASK_APP=run.py

WORKDIR /app

# Install system dependencies for Pillow and PostgreSQL client
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy backend application source
COPY . .

# Create uploads directory and runtime user
RUN mkdir -p /app/uploads && \
    groupadd -r civic && useradd -r -g civic -d /app civicuser && \
    chown -R civicuser:civic /app

USER civicuser

EXPOSE 5000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD curl -f http://localhost:5000/api/v1/public/stats || exit 1

CMD ["sh", "-c", "flask seed-db && gunicorn --bind 0.0.0.0:${PORT:-5000} --workers 2 --threads 2 --timeout 60 run:app"]
