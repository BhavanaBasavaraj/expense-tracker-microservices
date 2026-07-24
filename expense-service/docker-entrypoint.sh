#!/bin/sh
set -e

echo "Running Alembic Database Migrations for Expense Service..."
alembic upgrade head

exec "$@"
