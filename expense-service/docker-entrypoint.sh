#!/bin/sh
set -e

# Postgres can accept connections a moment before every database exists (first boot runs
# init.sql after the server is already reachable), so retry a bounded number of times.
# If migrations still fail, exit non-zero loudly: never start the service on a bad schema.
RETRIES="${MIGRATION_RETRIES:-10}"
DELAY="${MIGRATION_RETRY_DELAY:-2}"

echo "Running Alembic Database Migrations for Expense Service..."
attempt=1
until alembic upgrade head; do
  if [ "$attempt" -ge "$RETRIES" ]; then
    echo "ERROR: migrations failed after $attempt attempts; refusing to start." >&2
    exit 1
  fi
  echo "Migration attempt $attempt failed; retrying in ${DELAY}s..." >&2
  attempt=$((attempt + 1))
  sleep "$DELAY"
done

exec "$@"
