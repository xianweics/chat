from pydantic_settings import BaseSettings
from typing import Any

with open("../public.pem", "rb") as f:
    public_key = f.read()


class Settings(BaseSettings):
    APP_NAME: str = "llm_api_service"
    HOST: str = "localhost"
    PORT: int = 5003
    API_STR: str = "/llm"
    PUBLIC_KEY: Any = public_key
    ALGORITHM: str = "RS256"


settings = Settings()
