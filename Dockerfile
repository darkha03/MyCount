# Use an official Python runtime as a parent image
FROM python:3.13-slim AS base

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

RUN apt-get update \
 && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    pkg-config \
    default-libmysqlclient-dev \
 && rm -rf /var/lib/apt/lists/*

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# =========================
# Test stage (CI)
# =========================

FROM base AS test

# Install test dependencies
COPY requirements-dev.txt .
RUN pip install --no-cache-dir -r requirements-dev.txt

COPY . .

# Run tests
CMD ["pytest", "-q"]

# =========================
# Lint stage
# =========================

FROM base AS lint

# Install linting tools
COPY requirements-dev.txt .
RUN pip install --no-cache-dir -r requirements-dev.txt

COPY . .

# Run ruff lint
CMD ["ruff", "check", "."]

# =========================
# Development stage
# =========================

FROM base AS development

# Install development dependencies
COPY requirements-dev.txt .
RUN pip install --no-cache-dir -r requirements-dev.txt

COPY . .

# Run the application in development mode with auto-reload
CMD ["flask", "--app", "backend.app:create_app", "run", "--host=0.0.0.0", "--port", "5000", "--debug"]


# =========================
# Production stage
# =========================

FROM base AS production

# Install postgres client (for pg_isready)
RUN apt-get update \
 && apt-get install -y --no-install-recommends postgresql-client \
 && rm -rf /var/lib/apt/lists/*

# Copy only necessary files for production
COPY backend/ ./backend/
COPY migrations/ ./migrations/
COPY entrypoint.sh .

# Make entrypoint executable
RUN chmod +x entrypoint.sh

# Set entrypoint to run migrations before starting app
ENTRYPOINT ["./entrypoint.sh"]

# Run the application
CMD ["gunicorn", "-w", "3", "-b", "0.0.0.0:8000", "backend.app:create_app()"]