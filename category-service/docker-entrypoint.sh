#!/bin/sh
set -e

echo "Running Alembic Database Migrations for Category Service..."
alembic upgrade head

exec "$@"
