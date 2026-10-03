from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_title: str = "API working AI"
    token_api_ai: str
    ip_esp: str
    token_up: int = 10000
    token_down: int = 2000

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()
