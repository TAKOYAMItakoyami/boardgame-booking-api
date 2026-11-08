from pydantic import EmailStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_title: str = "Сервис Boardgame Booking API"
    description: str = "Сервис бронирования настольных игр"

    database_url: str | None = "sqlite+aiosqlite:///./bgb.db"

    postgres_user: str | None = None
    postgres_password: str | None = None
    postgres_db: str | None = None

    secret: str = "SECRET"
    jwt_lifetime: int = 3600
    first_superuser_email: EmailStr | None = None
    first_superuser_password: str | None = None

    yandex_disk_token: str | None = None
    report_format: str = "%Y.%m.%d %H:%M:%S"
    yandex_disk_base_url: str = "https://cloud-api.yandex.net/v1/disk"
    yandex_disk_timeout: float = 30.0

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()
