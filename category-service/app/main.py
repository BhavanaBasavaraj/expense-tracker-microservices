from fastapi import FastAPI
from app.database import engine, Base
from app.routers import categories

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Category Service", version="1.0.0")

app.include_router(categories.router)

@app.get("/health")
def health():
    return {"service": "category", "status": "healthy"}
