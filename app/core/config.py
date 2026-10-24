from pydantic import EmailStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_title: str = "Сервис Boardgame Booking API"
    description: str = "Сервис бронирования настольных игр"
    database_url: str | None = "sqlite+aiosqlite:///./bgb.db"
    secret: str = "SECRET"
    first_superuser_email: EmailStr | None = None
    first_superuser_password: str | None = None

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()
