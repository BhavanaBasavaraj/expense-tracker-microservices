from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import engine, Base
from app.routers import expenses

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Expense Service", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(expenses.router)

@app.get("/health")
def health():
    return {"service": "expense", "status": "healthy"}
