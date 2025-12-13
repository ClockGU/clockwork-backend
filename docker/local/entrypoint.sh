#!/bin/sh
set -e

echo "Waiting for database to be ready..."
# Wait for database to be ready
until nc -z clockwork-db 5432; do
  echo "Database is unavailable - sleeping"
  sleep 1
done

echo "Database is up - running migrations"
# Run alembic migrations
alembic upgrade head

echo "Starting application..."
# Execute the CMD from Dockerfile
exec "$@"
