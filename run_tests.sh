#!/usr/bin/env bash
set -e

echo "=================================================="
echo " 🧪 RUNNING MICROSERVICES TEST SUITES WITH COVERAGE"
echo "=================================================="

echo -e "\n[1/6] Testing Auth Service (Target >=95% Coverage)..."
DATABASE_URL=sqlite:///./auth_test.db PYTHONPATH=auth-service .venv/bin/pytest tests/test_auth_service.py tests/test_e2e_flow.py --cov=auth-service/app --cov-report=term-missing --cov-fail-under=95 -v

echo -e "\n[2/6] Testing Expense Service (Target >=95% Coverage)..."
DATABASE_URL=sqlite:///./expense_test.db PYTHONPATH=expense-service .venv/bin/pytest tests/test_expense_service.py --cov=expense-service/app --cov-report=term-missing --cov-fail-under=95 -v

echo -e "\n[3/6] Testing Category Service (Target >=95% Coverage)..."
DATABASE_URL=sqlite:///./category_test.db PYTHONPATH=category-service .venv/bin/pytest tests/test_category_service.py --cov=category-service/app --cov-report=term-missing --cov-fail-under=95 -v

echo -e "\n[4/6] Testing Analytics Service (Target >=95% Coverage)..."
PYTHONPATH=analytics-service .venv/bin/pytest tests/test_analytics_service.py --cov=analytics-service/app --cov-report=term-missing --cov-fail-under=95 -v

echo -e "\n[5/6] Testing API Gateway (Target >=95% Coverage)..."
PYTHONPATH=api-gateway .venv/bin/pytest tests/test_api_gateway.py --cov=api-gateway/app --cov-report=term-missing --cov-fail-under=95 -v

echo -e "\n[6/6] Testing Alembic Database Migrations..."
.venv/bin/pytest tests/test_alembic_migrations.py -v

echo -e "\n=================================================="
echo " 🎉 ALL MICROSERVICES PASSED WITH >95% CODE COVERAGE!"
echo "=================================================="
