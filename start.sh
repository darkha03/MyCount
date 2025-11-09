#!/usr/bin/env bash
set -euo pipefail

echo "Running diagnostic..."
python - <<'PY'
import os
from sqlalchemy import create_engine

raw_url = os.environ.get("DATABASE_URL")
print("Raw DATABASE_URL:", raw_url)

# Apply the same normalization as config.py
if raw_url and raw_url.startswith("postgres://"):
    raw_url = raw_url.replace("postgres://", "postgresql+psycopg://", 1)
elif raw_url and raw_url.startswith("postgresql://"):
    raw_url = raw_url.replace("postgresql://", "postgresql+psycopg://", 1)


try:
    engine = create_engine(raw_url)
    with engine.connect() as conn:
        result = conn.execute("select version()")
        print("Connected:", result.fetchone())
except Exception as e:
    print("Connection error:", e)
PY

echo "Running DB migrations..."
python - <<'PY'
from backend.app import create_app
from flask_migrate import upgrade

app = create_app()
with app.app_context():
    upgrade()
print("Migrations applied.")
PY

echo "Starting gunicorn..."
exec gunicorn --bind 0.0.0.0:${PORT:-8000} 'backend.app:create_app()'
