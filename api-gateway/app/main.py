from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Response, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from jose import jwt, JWTError
import httpx
from app.config import settings

limiter = Limiter(key_func=get_remote_address, default_limits=["120/minute"])

@asynccontextmanager
async def lifespan(app: FastAPI):
    limits = httpx.Limits(max_keepalive_connections=50, max_connections=200)
    timeout = httpx.Timeout(30.0, connect=5.0)
    app.state.http_client = httpx.AsyncClient(limits=limits, timeout=timeout)
    yield
    await app.state.http_client.aclose()

app = FastAPI(title="API Gateway", version="1.0.0", lifespan=lifespan)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def verify_and_extract_claims(auth_header: str):
    if not auth_header or not auth_header.startswith("Bearer "):
        return None
    token = auth_header.replace("Bearer ", "").strip()
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        user_id = payload.get("sub")
        email = payload.get("email", "")
        if user_id:
            return {"user_id": str(user_id), "email": str(email)}
    except (JWTError, ValueError, TypeError):
        pass
    return None

async def proxy(request: Request, target_url: str, require_auth: bool = False):
    # Header sanitization: Strip untrusted client X-User-* headers
    headers = {k: v for k, v in request.headers.items() if k.lower() not in ("host", "x-user-id", "x-user-email")}

    auth_header = request.headers.get("authorization")
    claims = verify_and_extract_claims(auth_header)
    
    if require_auth and not claims:
        raise HTTPException(status_code=401, detail="Invalid or missing authentication token")
    
    if claims:
        headers["X-User-ID"] = claims["user_id"]
        headers["X-User-Email"] = claims["email"]

    client: httpx.AsyncClient = getattr(request.app.state, "http_client", None)
    body = await request.body()
    
    try:
        if client:
            response = await client.request(
                method=request.method,
                url=target_url,
                headers=headers,
                params=dict(request.query_params),
                content=body
            )
        else:
            async with httpx.AsyncClient() as temp_client:
                response = await temp_client.request(
                    method=request.method,
                    url=target_url,
                    headers=headers,
                    params=dict(request.query_params),
                    content=body,
                    timeout=30.0
                )
        return Response(
            content=response.content,
            status_code=response.status_code,
            media_type=response.headers.get("content-type", "application/json")
        )
    except httpx.RequestError as exc:
        raise HTTPException(status_code=503, detail=f"Service unavailable: {str(exc)}")

# Auth routes with rate limiting
@app.api_route("/auth/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
@limiter.limit("10/minute")
async def auth_proxy(path: str, request: Request):
    return await proxy(request, f"{settings.auth_service_url}/auth/{path}")

@app.api_route("/auth", methods=["GET", "POST"])
@limiter.limit("10/minute")
async def auth_proxy_root(request: Request):
    return await proxy(request, f"{settings.auth_service_url}/auth/")

# Expense routes (Protected)
@app.api_route("/expenses/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def expense_proxy(path: str, request: Request):
    return await proxy(request, f"{settings.expense_service_url}/expenses/{path}", require_auth=True)

@app.api_route("/expenses", methods=["GET", "POST", "PUT", "DELETE"])
async def expense_proxy_root(request: Request):
    return await proxy(request, f"{settings.expense_service_url}/expenses/", require_auth=True)

# Category routes (Protected)
@app.api_route("/categories/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def category_proxy(path: str, request: Request):
    return await proxy(request, f"{settings.category_service_url}/categories/{path}", require_auth=True)

@app.api_route("/categories", methods=["GET", "POST", "PUT", "DELETE"])
async def category_proxy_root(request: Request):
    return await proxy(request, f"{settings.category_service_url}/categories/", require_auth=True)

# Analytics routes (Protected)
@app.api_route("/analytics/{path:path}", methods=["GET"])
async def analytics_proxy(path: str, request: Request):
    return await proxy(request, f"{settings.analytics_service_url}/analytics/{path}", require_auth=True)

@app.api_route("/analytics", methods=["GET"])
async def analytics_proxy_root(request: Request):
    return await proxy(request, f"{settings.analytics_service_url}/analytics/", require_auth=True)

@app.get("/health")
async def health():
    results = {}
    services = {
        "auth": f"{settings.auth_service_url}/health",
        "expense": f"{settings.expense_service_url}/health",
        "category": f"{settings.category_service_url}/health",
        "analytics": f"{settings.analytics_service_url}/health",
    }
    client: httpx.AsyncClient = getattr(app.state, "http_client", None)
    if client:
        for name, url in services.items():
            try:
                r = await client.get(url, timeout=5.0)
                results[name] = "healthy" if r.status_code == 200 else "unhealthy"
            except:
                results[name] = "unreachable"
    else:
        async with httpx.AsyncClient() as temp_client:
            for name, url in services.items():
                try:
                    r = await temp_client.get(url, timeout=5.0)
                    results[name] = "healthy" if r.status_code == 200 else "unhealthy"
                except:
                    results[name] = "unreachable"
    return {"gateway": "healthy", "services": results}

@app.get("/")
def root():
    return {"message": "Expense Tracker API Gateway", "version": "1.0.0"}
