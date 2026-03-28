from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import engine, Base
from app.routers import categories

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Category Service", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(categories.router)

@app.get("/health")
def health():
    return {"service": "category", "status": "healthy"}
