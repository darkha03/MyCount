#!/usr/bin/env bash
set -euo pipefail

echo "Running diagnostic..."
python - <<'PY'
import os, psycopg
url = os.environ.get("DATABASE_URL")
print("Raw DATABASE_URL:", url)
try:
    with psycopg.connect(url) as conn:
        with conn.cursor() as cur:
            cur.execute("select version()")
            print("Connected:", cur.fetchone())
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
