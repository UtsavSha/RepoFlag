from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # App Settings
    PROJECT_NAME: str = "RepoFlag"

    # External APIs (Removed OpenAI, strictly using Google GenAI now)
    GOOGLE_API_KEY: str | None = None

    # Database (Keeping repoflag.db so you don't lose your existing scanned data,
    # but you can change this to sqlite:///repoflag.db if you want a fresh start!)
    DATABASE_URL: str = "sqlite:///repoflag.db"

    # Future Auth (Phase 2)
    SECRET_KEY: str = "change_this_in_production"
    ALGORITHM: str = "HS256"

    # This tells Pydantic to read from your .env file
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore")


# Create a global instance to import across the app
settings = Settings()
