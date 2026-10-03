from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


ENV_FILE = Path(__file__).resolve().parents[1] / ".env"


class Settings(BaseSettings):
    app_title: str = "ESP AI Voice Bridge"
    host: str = "0.0.0.0"
    port: int = 8000
    token_api_ai: str = ""
    esp_api_key: str = Field(min_length=16)
    realtime_model: str = "gpt-realtime-2.1"
    realtime_voice: str = "marin"
    # Kept for compatibility with the project's existing .env file.
    ip_esp: str | None = None

    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
