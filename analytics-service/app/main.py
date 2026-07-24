from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import httpx
from app.routers import analytics

@asynccontextmanager
async def lifespan(app: FastAPI):
    limits = httpx.Limits(max_keepalive_connections=20, max_connections=50)
    timeout = httpx.Timeout(10.0, connect=3.0)
    app.state.http_client = httpx.AsyncClient(limits=limits, timeout=timeout)
    yield
    await app.state.http_client.aclose()

app = FastAPI(title="Analytics Service", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(analytics.router)

@app.get("/health")
def health():
    return {"service": "analytics", "status": "healthy"}
