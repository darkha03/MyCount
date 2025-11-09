#!/usr/bin/env bash
set -euo pipefail

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
