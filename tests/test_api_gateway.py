import pytest
from fastapi.testclient import TestClient
import sys, os
from jose import jwt
import httpx

sys.path.insert(0, os.path.abspath("api-gateway"))

from app.main import app, verify_and_extract_claims, proxy
from app.config import settings

def create_valid_token(user_id=1, email="test@example.com"):
    payload = {"sub": str(user_id), "email": email}
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)

def test_verify_and_extract_claims_valid():
    token = create_valid_token(user_id=42, email="user42@example.com")
    claims = verify_and_extract_claims(f"Bearer {token}")
    assert claims is not None
    assert claims["user_id"] == "42"
    assert claims["email"] == "user42@example.com"

def test_verify_and_extract_claims_invalid():
    assert verify_and_extract_claims(None) is None
    assert verify_and_extract_claims("Basic xyz") is None
    assert verify_and_extract_claims("Bearer invalid.jwt.token") is None

def test_gateway_root():
    with TestClient(app) as client:
        response = client.get("/")
        assert response.status_code == 200
        assert response.json()["message"] == "Expense Tracker API Gateway"

def test_gateway_protected_route_unauthorized():
    with TestClient(app) as client:
        response = client.get("/expenses/")
        assert response.status_code == 401
        assert "Invalid or missing authentication token" in response.json()["detail"]

def test_gateway_proxy_success(httpx_mock):
    token = create_valid_token(10, "proxy@example.com")
    
    httpx_mock.add_response(
        method="GET",
        url=f"{settings.expense_service_url}/expenses/",
        status_code=200,
        json=[{"id": 1, "title": "Coffee", "amount": 5.0}]
    )

    with TestClient(app) as client:
        response = client.get(
            "/expenses/",
            headers={
                "Authorization": f"Bearer {token}",
                "X-User-ID": "spoofed_id",
                "X-Internal-Key": "client-supplied-guess",
            }
        )
        assert response.status_code == 200
        assert response.json() == [{"id": 1, "title": "Coffee", "amount": 5.0}]
        
        request = httpx_mock.get_request()
        assert request.headers["X-User-ID"] == "10"
        assert request.headers["X-User-Email"] == "proxy@example.com"
        # The gateway, not the client, decides the internal key; the raw token is not forwarded.
        assert request.headers["X-Internal-Key"] == settings.internal_api_key
        assert request.headers["X-Internal-Key"] != "client-supplied-guess"
        assert "authorization" not in request.headers

def test_gateway_proxy_fallback_temp_client(httpx_mock):
    token = create_valid_token(10, "fallback@example.com")
    
    httpx_mock.add_response(
        method="GET",
        url=f"{settings.expense_service_url}/expenses/",
        status_code=200,
        json=[{"id": 1, "title": "Coffee", "amount": 5.0}]
    )

    # Remove http_client to force fallback path
    if hasattr(app.state, "http_client"):
        delattr(app.state, "http_client")

    client = TestClient(app)
    response = client.get(
        "/expenses/",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200

def test_gateway_proxy_subpath_routes(httpx_mock):
    token = create_valid_token(1, "demo@example.com")
    
    httpx_mock.add_response(
        method="POST",
        url=f"{settings.category_service_url}/categories/item",
        status_code=201,
        json={"id": 1, "name": "Groceries"}
    )
    with TestClient(app) as client:
        response = client.post(
            "/categories/item",
            headers={"Authorization": f"Bearer {token}"},
            json={"name": "Groceries"}
        )
        assert response.status_code == 201

def test_gateway_analytics_proxy(httpx_mock):
    token = create_valid_token(1, "demo@example.com")
    
    httpx_mock.add_response(
        method="GET",
        url=f"{settings.analytics_service_url}/analytics/dashboard",
        status_code=200,
        json={"total_income": 1000.0}
    )
    httpx_mock.add_response(
        method="GET",
        url=f"{settings.analytics_service_url}/analytics/",
        status_code=200,
        json={"status": "ok"}
    )
    
    with TestClient(app) as client:
        r1 = client.get("/analytics/dashboard", headers={"Authorization": f"Bearer {token}"})
        assert r1.status_code == 200
        assert r1.json()["total_income"] == 1000.0

        r2 = client.get("/analytics", headers={"Authorization": f"Bearer {token}"})
        assert r2.status_code == 200

def test_gateway_auth_proxy(httpx_mock):
    httpx_mock.add_response(
        method="POST",
        url=f"{settings.auth_service_url}/auth/login",
        status_code=200,
        json={"access_token": "abc"}
    )
    httpx_mock.add_response(
        method="GET",
        url=f"{settings.auth_service_url}/auth/me",
        status_code=200,
        json={"id": 1}
    )
    
    with TestClient(app) as client:
        r1 = client.post("/auth/login", json={"email": "a@b.com", "password": "p"})
        assert r1.status_code == 200
        
        r2 = client.get("/auth/me")
        assert r2.status_code == 200

def test_gateway_proxy_service_unavailable(httpx_mock):
    httpx_mock.add_exception(
        httpx.RequestError("Connection refused"),
        url=f"{settings.auth_service_url}/auth/"
    )
    with TestClient(app) as client:
        response = client.get("/auth")
        assert response.status_code == 503
        assert "Service unavailable" in response.json()["detail"]

def test_gateway_health_with_lifespan(httpx_mock):
    httpx_mock.add_response(url=f"{settings.auth_service_url}/health", status_code=200)
    httpx_mock.add_response(url=f"{settings.expense_service_url}/health", status_code=500)
    httpx_mock.add_response(url=f"{settings.category_service_url}/health", status_code=200)
    httpx_mock.add_exception(httpx.RequestError("Down"), url=f"{settings.analytics_service_url}/health")

    with TestClient(app) as client:
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["gateway"] == "healthy"
        assert data["services"]["auth"] == "healthy"
        assert data["services"]["expense"] == "unhealthy"
        assert data["services"]["category"] == "healthy"
        assert data["services"]["analytics"] == "unreachable"
        assert data["services"]["redis"] == "memory"  # unit tests use memory:// storage

def test_gateway_health_fallback_temp_client(httpx_mock):
    if hasattr(app.state, "http_client"):
        delattr(app.state, "http_client")

    httpx_mock.add_response(url=f"{settings.auth_service_url}/health", status_code=200)
    httpx_mock.add_response(url=f"{settings.expense_service_url}/health", status_code=200)
    httpx_mock.add_response(url=f"{settings.category_service_url}/health", status_code=200)
    httpx_mock.add_response(url=f"{settings.analytics_service_url}/health", status_code=200)

    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["services"]["auth"] == "healthy"


# ------------------------------------------------------------------ auth strength

def test_token_signed_with_wrong_secret_is_rejected():
    forged = jwt.encode({"sub": "1", "email": "x@y.z"}, "not-the-real-secret", algorithm="HS256")
    assert verify_and_extract_claims(f"Bearer {forged}") is None
    with TestClient(app) as client:
        assert client.get("/expenses/", headers={"Authorization": f"Bearer {forged}"}).status_code == 401


def test_unsigned_alg_none_token_is_rejected():
    import base64, json
    def b64(d):
        return base64.urlsafe_b64encode(json.dumps(d).encode()).rstrip(b"=").decode()
    unsigned = f"{b64({'alg': 'none', 'typ': 'JWT'})}.{b64({'sub': '1'})}."
    assert verify_and_extract_claims(f"Bearer {unsigned}") is None


def test_expired_token_is_rejected():
    expired = jwt.encode({"sub": "1", "email": "x@y.z", "exp": 1}, settings.secret_key, algorithm=settings.algorithm)
    assert verify_and_extract_claims(f"Bearer {expired}") is None


def test_client_cannot_inject_identity_without_a_token(httpx_mock):
    """Forged X-User-ID with no valid token must not reach a protected service at all."""
    with TestClient(app) as client:
        res = client.get("/expenses/", headers={"X-User-ID": "1", "X-Internal-Key": settings.internal_api_key})
    assert res.status_code == 401
    assert httpx_mock.get_requests() == []


# ------------------------------------------------------------------ rate limiting + redis

def test_auth_endpoints_are_rate_limited_at_10_per_minute(httpx_mock):
    from app.main import limiter
    limiter.reset()
    httpx_mock.add_response(method="POST", url=f"{settings.auth_service_url}/auth/login",
                            status_code=401, is_reusable=True, json={"detail": "nope"})
    with TestClient(app) as client:
        statuses = [client.post("/auth/login", json={}).status_code for _ in range(12)]
    assert statuses[:10] == [401] * 10
    assert statuses[10:] == [429, 429]
    limiter.reset()


def test_check_redis_raises_when_redis_is_unreachable():
    from app.main import check_redis
    with pytest.raises(Exception):
        check_redis("redis://127.0.0.1:1/0")  # nothing listens on port 1


def test_gateway_refuses_to_start_when_redis_is_unreachable(monkeypatch):
    monkeypatch.setattr(settings, "redis_url", "redis://127.0.0.1:1/0")
    with pytest.raises(Exception):
        with TestClient(app):
            pass


def test_gateway_refuses_to_start_without_internal_key(monkeypatch):
    monkeypatch.setattr(settings, "internal_api_key", "")
    with pytest.raises(RuntimeError, match="INTERNAL_API_KEY"):
        with TestClient(app):
            pass


def test_health_reports_redis_unreachable_instead_of_hiding_it(httpx_mock, monkeypatch):
    for svc in (settings.auth_service_url, settings.expense_service_url,
                settings.category_service_url, settings.analytics_service_url):
        httpx_mock.add_response(url=f"{svc}/health", status_code=200)
    with TestClient(app) as client:  # starts fine on memory://
        monkeypatch.setattr(settings, "redis_url", "redis://127.0.0.1:1/0")
        data = client.get("/health").json()
    assert data["services"]["redis"] == "unreachable"
