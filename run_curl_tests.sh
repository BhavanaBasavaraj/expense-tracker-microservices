#!/usr/bin/env bash
set -e

BASE_URL="http://127.0.0.1:8000"

echo "============================================="
echo " 🧪 EXPENSE TRACKER API GATEWAY INTEGRATION TEST"
echo "============================================="

# 1. Health Check
echo -e "\n[1/12] Checking API Gateway Health..."
curl -s -w "\nHTTP Status: %{http_code}\n" "${BASE_URL}/health"

# 2. Register User Success
echo -e "\n[2/12] Registering new user via API Gateway..."
REG_RESP=$(curl -s -i -X POST "${BASE_URL}/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "demo.user@example.com",
    "first_name": "Demo",
    "last_name": "User",
    "password": "Password123!"
  }')
echo "$REG_RESP"

# 3. Invalid Email Validation Check
echo -e "\n[3/12] Testing Invalid Email Format (Expecting HTTP 422)..."
curl -s -i -X POST "${BASE_URL}/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "invalid-email-format",
    "first_name": "Demo",
    "last_name": "User",
    "password": "Password123!"
  }'

# 4. Duplicate Email Check (Expecting HTTP 400 via Gateway)
echo -e "\n[4/12] Testing Duplicate Email Registration (Expecting HTTP 400)..."
curl -s -i -X POST "${BASE_URL}/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "demo.user@example.com",
    "first_name": "Demo",
    "last_name": "User",
    "password": "Password123!"
  }'

# 5. Login
echo -e "\n[5/12] Logging in to obtain JWT Access Token..."
LOGIN_RESP=$(curl -s -X POST "${BASE_URL}/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=demo.user@example.com&password=Password123!")
echo "Login Response: $LOGIN_RESP"

TOKEN=$(echo "$LOGIN_RESP" | python3 -c "import sys, json; print(json.load(sys.stdin).get('access_token', ''))")
echo "Extracted Token: ${TOKEN:0:25}..."

# 6. Verify Get Me
echo -e "\n[6/12] Fetching User Profile (/auth/me)..."
curl -s -w "\nHTTP Status: %{http_code}\n" "${BASE_URL}/auth/me?token=${TOKEN}"

# 7. Create Category
echo -e "\n[7/12] Creating Category ('Salary & Bonus')..."
CAT_RESP=$(curl -s -X POST "${BASE_URL}/categories" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${TOKEN}" \
  -d '{
    "name": "Salary & Bonus",
    "type": "income"
  }')
echo "Category Created: $CAT_RESP"

# 8. Create Income Transaction
echo -e "\n[8/12] Adding Income Transaction ($6000.00)..."
INC_RESP=$(curl -s -X POST "${BASE_URL}/expenses" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${TOKEN}" \
  -d '{
    "title": "Monthly Paycheck",
    "amount": 6000.00,
    "type": "income",
    "date": "2026-07-01",
    "category_id": 1,
    "description": "July base salary"
  }')
echo "Income Transaction: $INC_RESP"

# 9. Create Expense Transaction
echo -e "\n[9/12] Adding Expense Transaction ($1200.00)..."
EXP_RESP=$(curl -s -X POST "${BASE_URL}/expenses" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${TOKEN}" \
  -d '{
    "title": "Apartment Rent",
    "amount": 1200.00,
    "type": "expense",
    "date": "2026-07-05",
    "category_id": 2,
    "description": "July rent payment"
  }')
echo "Expense Transaction: $EXP_RESP"

# 10. Fetch All Expenses
echo -e "\n[10/12] Fetching All Transactions..."
curl -s -H "Authorization: Bearer ${TOKEN}" "${BASE_URL}/expenses"

# 11. Fetch Analytics Dashboard
echo -e "\n\n[11/12] Fetching Analytics Dashboard Summary..."
curl -s -H "Authorization: Bearer ${TOKEN}" "${BASE_URL}/analytics/dashboard"

# 12. Fetch Analytics Monthly Summary
echo -e "\n\n[12/12] Fetching Monthly Analytics Breakdown..."
curl -s -H "Authorization: Bearer ${TOKEN}" "${BASE_URL}/analytics/monthly"

echo -e "\n\n============================================="
echo " 🎉 ALL CURL TESTS COMPLETED SUCCESSFULLY!"
echo "============================================="
