from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    auth_service_url: str = "http://auth-service:8001"
    expense_service_url: str = "http://expense-service:8002"

    class Config:
        env_file = ".env"

settings = Settings()
