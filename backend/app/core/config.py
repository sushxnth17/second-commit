from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    github_client_id: str
    github_client_secret: str
    session_secret: str
    database_url: str
    groq_api_key: str | None = None
    groq_model: str = "llama3-8b-8192"

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore"
    )


settings = Settings()