#!/bin/sh
set -e

echo "Waiting for PostgreSQL..."

until pg_isready -h db -p 5432 -U "$POSTGRES_USER"; do
  sleep 1
done

echo "PostgreSQL started"

echo "Database is up - running migrations..."
flask --app backend.app:create_app db upgrade

echo "Starting application..."
exec "$@"
