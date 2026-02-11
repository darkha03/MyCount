#!/bin/sh
set -e

echo "Waiting for database to be ready..."
until python -c "from backend.app import create_app; app = create_app(); app.app_context().push(); from backend import db; db.engine.connect()" 2>/dev/null; do
  echo "Database is unavailable - sleeping"
  sleep 2
done

echo "Database is up - running migrations..."
flask --app backend.app:create_app db upgrade

echo "Starting application..."
exec "$@"
