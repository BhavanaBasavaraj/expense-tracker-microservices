#!/usr/bin/env bash
set -e

echo "=================================================="
echo " 🧪 RUNNING MICROSERVICES UNIT & INTEGRATION TESTS"
echo "=================================================="

echo -e "\n[1/4] Testing Auth Service & E2E Auth Flow..."
DATABASE_URL=sqlite:///./auth_test.db PYTHONPATH=auth-service .venv/bin/pytest tests/test_auth_service.py tests/test_e2e_flow.py -v

echo -e "\n[2/4] Testing Expense Service..."
DATABASE_URL=sqlite:///./expense_test.db PYTHONPATH=expense-service .venv/bin/pytest tests/test_expense_service.py -v

echo -e "\n[3/4] Testing Category Service..."
DATABASE_URL=sqlite:///./category_test.db PYTHONPATH=category-service .venv/bin/pytest tests/test_category_service.py -v

echo -e "\n[4/5] Testing Analytics Service..."
PYTHONPATH=analytics-service .venv/bin/pytest tests/test_analytics_service.py -v

echo -e "\n[5/5] Testing API Gateway..."
PYTHONPATH=api-gateway .venv/bin/pytest tests/test_api_gateway.py -v

echo -e "\n=================================================="
echo " ✅ ALL MICROSERVICES TEST SUITES PASSED CLEANLY!"
echo "=================================================="
