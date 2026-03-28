from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str = "postgresql://bhavana:postgres@localhost:5432/category_db"
    auth_service_url: str = "http://auth-service:8001"

    class Config:
        env_file = ".env"

settings = Settings()
