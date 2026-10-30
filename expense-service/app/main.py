from fastapi import FastAPI
from app.database import engine, Base
from app.routers import expenses

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Expense Service", version="1.0.0")

app.include_router(expenses.router)

@app.get("/health")
def health():
    return {"service": "expense", "status": "healthy"}
