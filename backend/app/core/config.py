from functools import lru_cache
from typing import List

from pydantic import AnyUrl
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "Traya Product Discovery Assistant"
    environment: str = "development"

    # Core services
    database_url: str
    openai_api_key: str
    # Optional custom base URL for OpenAI-compatible APIs (e.g. Groq)
    openai_base_url: str | None = None

    # Vector store
    chroma_path: str = "./chroma_db"

    # CORS
    cors_origins: List[AnyUrl] = []

    # DuckDuckGo via SearchApi.io
    searchapi_api_key: str | None = None
    searchapi_base_url: str = "https://www.searchapi.io/api/v1/search"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]


