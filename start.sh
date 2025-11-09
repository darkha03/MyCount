#!/usr/bin/env bash
set -euo pipefail

echo "Running diagnostic..."
python - <<'PY'
import os
from urllib.parse import urlparse

raw = os.environ.get("DATABASE_URL")
print("Raw URL:", raw[:50] + "..." if len(raw) > 50 else raw)

try:
    parsed = urlparse(raw)
    print(f"Scheme: {parsed.scheme}")
    print(f"Username: {parsed.username}")
    print(f"Password: {'***' if parsed.password else None}")
    print(f"Hostname: {parsed.hostname}")
    print(f"Port: {parsed.port}")
    print(f"Path: {parsed.path}")
except Exception as e:
    print("Parse error:", e)
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
