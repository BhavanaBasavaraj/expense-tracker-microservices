from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str = "postgresql://bhavana:postgres@localhost:5432/category_db"

    # Shared secret the API gateway attaches to proxied requests. Empty = fail closed.
    internal_api_key: str = ""

    class Config:
        env_file = ".env"

settings = Settings()
