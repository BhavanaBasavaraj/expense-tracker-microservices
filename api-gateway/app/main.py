from fastapi import FastAPI, Request, Response, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import httpx
from app.config import settings

limiter = Limiter(key_func=get_remote_address, default_limits=["120/minute"])

app = FastAPI(title="API Gateway", version="1.0.0")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

async def proxy(request: Request, target_url: str):
    async with httpx.AsyncClient() as client:
        body = await request.body()
        headers = {k: v for k, v in request.headers.items() if k.lower() != "host"}
        try:
            response = await client.request(
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

# Expense routes
@app.api_route("/expenses/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def expense_proxy(path: str, request: Request):
    return await proxy(request, f"{settings.expense_service_url}/expenses/{path}")

@app.api_route("/expenses", methods=["GET", "POST", "PUT", "DELETE"])
async def expense_proxy_root(request: Request):
    return await proxy(request, f"{settings.expense_service_url}/expenses/")

# Category routes
@app.api_route("/categories/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def category_proxy(path: str, request: Request):
    return await proxy(request, f"{settings.category_service_url}/categories/{path}")

@app.api_route("/categories", methods=["GET", "POST", "PUT", "DELETE"])
async def category_proxy_root(request: Request):
    return await proxy(request, f"{settings.category_service_url}/categories/")

# Analytics routes
@app.api_route("/analytics/{path:path}", methods=["GET"])
async def analytics_proxy(path: str, request: Request):
    return await proxy(request, f"{settings.analytics_service_url}/analytics/{path}")

@app.api_route("/analytics", methods=["GET"])
async def analytics_proxy_root(request: Request):
    return await proxy(request, f"{settings.analytics_service_url}/analytics/")

@app.get("/health")
async def health():
    results = {}
    services = {
        "auth": f"{settings.auth_service_url}/health",
        "expense": f"{settings.expense_service_url}/health",
        "category": f"{settings.category_service_url}/health",
        "analytics": f"{settings.analytics_service_url}/health",
    }
    async with httpx.AsyncClient() as client:
        for name, url in services.items():
            try:
                r = await client.get(url, timeout=5.0)
                results[name] = "healthy" if r.status_code == 200 else "unhealthy"
            except:
                results[name] = "unreachable"
    return {"gateway": "healthy", "services": results}

@app.get("/")
def root():
    return {"message": "Expense Tracker API Gateway", "version": "1.0.0"}
