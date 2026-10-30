from fastapi import FastAPI
from app.database import engine, Base
from app.routers import auth

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Auth Service", version="1.0.0")

app.include_router(auth.router)

@app.get("/health")
def health():
    return {"service": "auth", "status": "healthy"}
