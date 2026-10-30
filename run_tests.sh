#!/usr/bin/env bash
# Runs every backend suite with a hard coverage gate. The same script runs locally and in CI.
#   pip install -r auth-service/requirements.txt -r expense-service/requirements.txt \
#               -r category-service/requirements.txt -r analytics-service/requirements.txt \
#               -r api-gateway/requirements.txt -r requirements-dev.txt
#   ./run_tests.sh
# Optional: REDIS_TEST_URL=redis://localhost:6379/15 also runs the real-Redis integration test.
set -euo pipefail

PYTEST="python -m pytest -q -W ignore"
GATE=95
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

run_suite() {
  local name="$1" dir="$2"; shift 2
  echo -e "\n=== $name (coverage must be >= ${GATE}%) ==="
  PYTHONPATH="$dir" $PYTEST "$@" --cov="$dir/app" --cov-report=term-missing --cov-fail-under=$GATE
}

DATABASE_URL="sqlite:///$TMP/auth.db"     run_suite "Auth Service"     auth-service     tests/test_auth_service.py tests/test_e2e_flow.py
DATABASE_URL="sqlite:///$TMP/expense.db"  run_suite "Expense Service"  expense-service  tests/test_expense_service.py
DATABASE_URL="sqlite:///$TMP/category.db" run_suite "Category Service" category-service tests/test_category_service.py
run_suite "Analytics Service" analytics-service tests/test_analytics_service.py
run_suite "API Gateway"       api-gateway       tests/test_api_gateway.py

echo -e "\n=== Alembic migrations (schema + model drift) ==="
$PYTEST tests/test_alembic_migrations.py

echo -e "\n=== Gateway <-> real Redis ==="
PYTHONPATH=api-gateway $PYTEST tests/test_gateway_redis_integration.py -rs

echo -e "\nAll backend suites passed with >=${GATE}% coverage per service."
