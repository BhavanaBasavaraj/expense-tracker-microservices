from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    expense_service_url: str = "http://expense-service:8002"

    # Shared secret the API gateway attaches to proxied requests. Empty = fail closed.
    internal_api_key: str = ""

    class Config:
        env_file = ".env"

settings = Settings()
