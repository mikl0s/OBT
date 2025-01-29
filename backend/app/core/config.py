"""Application configuration."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""

    # Project Info
    PROJECT_NAME: str = "Ollama Benchmark Tool"
    VERSION: str = "0.0.0"
    API_V1_PREFIX: str = "/api/v1"

    # MongoDB
    MONGO_HOST: str = "localhost"
    MONGO_PORT: int = 27017
    MONGO_USER: str = "obt_user"
    MONGO_PASSWORD: str = "obt_password"
    MONGO_DB: str = "obt_db"

    # Server
    BACKEND_HOST: str = "0.0.0.0"
    BACKEND_PORT: int = 8000
    LOG_LEVEL: str = "info"

    @property
    def mongodb_url(self) -> str:
        """Get MongoDB connection URL."""
        return (
            f"mongodb://{self.MONGO_USER}:{self.MONGO_PASSWORD}"
            f"@{self.MONGO_HOST}:{self.MONGO_PORT}/{self.MONGO_DB}"
        )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )


settings = Settings()
