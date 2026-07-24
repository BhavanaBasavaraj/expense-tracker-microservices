from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    auth_service_url: str = "http://auth-service:8001"
    expense_service_url: str = "http://expense-service:8002"
    category_service_url: str = "http://category-service:8003"
    analytics_service_url: str = "http://analytics-service:8004"
    redis_url: str = "redis://redis:6379/0"

    class Config:
        env_file = ".env"

settings = Settings()
