#!/usr/bin/env bash
# End-to-end smoke test against a RUNNING stack (docker compose up, or local processes).
#   BASE_URL=http://127.0.0.1:8000 ./scripts/smoke_test.sh
#   CHECK_INTERNAL_PORTS_CLOSED=1 ./scripts/smoke_test.sh    # compose only: 8001-8004 must not be reachable
set -euo pipefail

BASE_URL="${BASE_URL:-http://127.0.0.1:8000}"
RUN_ID="$(date +%s)$RANDOM"
PASS=0

ok()   { echo "  ok   - $1"; PASS=$((PASS+1)); }
fail() { echo "  FAIL - $1"; exit 1; }
code() { curl -s -o /dev/null -w '%{http_code}' "$@"; }
json() { python3 -c "import sys,json; print(json.load(sys.stdin)$1)"; }

echo "Waiting for gateway at $BASE_URL ..."
for i in $(seq 1 60); do
  if body=$(curl -sf "$BASE_URL/health" 2>/dev/null) && echo "$body" | python3 -c "
import sys,json
d=json.load(sys.stdin)
bad=[k for k,v in d['services'].items() if v not in ('healthy','memory')]
sys.exit(1 if bad else 0)"; then break; fi
  [ "$i" = 60 ] && { echo "$body"; fail "stack did not become healthy in 60s"; }
  sleep 1
done
ok "gateway reports all services and redis healthy"

register() { curl -sf -X POST "$BASE_URL/auth/register" -H 'Content-Type: application/json' \
  -d "{\"email\":\"$1\",\"first_name\":\"S\",\"last_name\":\"T\",\"password\":\"Passw0rd!123\"}" >/dev/null; }
login() { curl -sf -X POST "$BASE_URL/auth/login" -d "username=$1&password=Passw0rd!123" | json "['access_token']"; }

A="a-$RUN_ID@example.com"; B="b-$RUN_ID@example.com"
register "$A"; register "$B"; ok "registered two users"
TA=$(login "$A"); TB=$(login "$B"); ok "both users logged in (JWT issued)"

EXP='{"title":"smoke-expense","amount":12.5,"type":"expense","date":"2026-01-15"}'
[ "$(code -X POST "$BASE_URL/expenses/" -H "Authorization: Bearer $TA" -H 'Content-Type: application/json' -d "$EXP")" = 200 ] \
  && ok "user A created an expense through the gateway" || fail "create expense"

curl -sf "$BASE_URL/expenses/" -H "Authorization: Bearer $TA" | grep -q smoke-expense \
  && ok "user A can read their expense" || fail "A cannot read own expense"
curl -sf "$BASE_URL/expenses/" -H "Authorization: Bearer $TB" | grep -q smoke-expense \
  && fail "TENANT LEAK: user B can see user A's expense" || ok "user B cannot see user A's expense"

[ "$(curl -sf "$BASE_URL/analytics/dashboard" -H "Authorization: Bearer $TA" | json "['total_expenses']")" = "12.5" ] \
  && ok "analytics (gateway -> analytics -> expense) returns A's total" || fail "analytics total"

[ "$(code "$BASE_URL/expenses/")" = 401 ] && ok "no token -> 401" || fail "unauthenticated request accepted"
[ "$(code "$BASE_URL/expenses/" -H 'X-User-ID: 1' -H 'X-Internal-Key: guess')" = 401 ] \
  && ok "forged identity headers without a token -> 401" || fail "forged headers accepted"
[ "$(code "$BASE_URL/expenses/" -H 'Authorization: Bearer not.a.jwt')" = 401 ] \
  && ok "garbage JWT -> 401" || fail "garbage JWT accepted"

if [ "${CHECK_INTERNAL_PORTS_CLOSED:-0}" = 1 ]; then
  for port in 8001 8002 8003 8004; do
    if curl -s --max-time 2 -o /dev/null "http://127.0.0.1:$port/health"; then fail "internal port $port is reachable from the host"; fi
  done
  ok "internal service ports 8001-8004 are not published"
fi

echo "All $PASS smoke checks passed."
