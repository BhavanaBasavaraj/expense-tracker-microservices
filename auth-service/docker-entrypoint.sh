#!/bin/sh
set -e

echo "Running Alembic Database Migrations for Auth Service..."
alembic upgrade head

exec "$@"
