from http import HTTPStatus

import httpx
from fastapi import HTTPException

from app.core.config import settings
from app.core.constants import (
    REPORTS_FOLDER_DEFAULT,
    YANDEX_DISK_PATH_PREFIX,
    YANDEX_DISK_PUBLISH_ENDPOINT,
    YANDEX_DISK_RESOURCES_ENDPOINT,
    YANDEX_DISK_UPLOAD_ENDPOINT,
)


class YandexDiskClient:
    """Клиент для API Яндекс Диска"""

    def __init__(self, token: str):
        self.token = token
        self.base_url = settings.yandex_disk_base_url
        self.upload_endpoint = f"{self.base_url}{YANDEX_DISK_UPLOAD_ENDPOINT}"
        self.publish_endpoint = (
            f"{self.base_url}{YANDEX_DISK_PUBLISH_ENDPOINT}"
        )
        self.resources_endpoint = (
            f"{self.base_url}{YANDEX_DISK_RESOURCES_ENDPOINT}"
        )
        self.headers = {"Authorization": f"OAuth {token}"}
        self._client: httpx.AsyncClient | None = None

    @property
    def client(self) -> httpx.AsyncClient:
        """Возвращает клиент, гарантируя, что он инициализирован"""
        if self._client is None:
            raise RuntimeError("Яндекс клиент не инициализирован!")
        return self._client

    async def __aenter__(self):
        self._client = httpx.AsyncClient(timeout=settings.yandex_disk_timeout)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._client:
            await self._client.aclose()

    async def create_excel_file(
        self, title: str, folder: str = REPORTS_FOLDER_DEFAULT
    ) -> tuple[str, str]:
        """
        Создаёт Excel-файл и возвращает ссылку для загрузки и путь к файлу
        """
        await self._create_folder(folder)

        file_path = f"{YANDEX_DISK_PATH_PREFIX}{folder}/{title}.xlsx"

        response = await self.client.get(
            self.upload_endpoint,
            headers=self.headers,
            params={"path": file_path, "overwrite": "true"},
        )
        response.raise_for_status()

        data = response.json()
        upload_url = data.get("href")

        if not upload_url:
            raise ValueError("Не удалось получить ссылку для загрузки")

        return upload_url, file_path

    async def upload_file(self, upload_url: str, content: bytes):
        """Загружает файл по полученной ссылке"""
        response = await self.client.put(
            upload_url,
            content=content,
            headers={
                "Content-Type": (
                    "application/vnd.openxmlformats-officedocument."
                    "spreadsheetml.sheet"
                )
            },
        )
        response.raise_for_status()

    async def _publish_file(self, file_path: str) -> None:
        """Делает файл публичным."""
        response = await self.client.put(
            self.publish_endpoint,
            headers=self.headers,
            params={"path": file_path},
        )
        response.raise_for_status()

    async def publish_file(self, file_path: str) -> str:
        """Делает файл публичным и возвращает публичную ссылку."""
        await self._publish_file(file_path)
        response = await self.client.get(
            self.resources_endpoint,
            headers=self.headers,
            params={"path": file_path},
        )
        response.raise_for_status()

        data = response.json()
        public_url = data.get("public_url")

        if not public_url:
            raise HTTPException(
                status_code=HTTPStatus.SERVICE_UNAVAILABLE,
                detail="Ссылка не была получена со стороны Яндекс Диска",
            )

        return public_url

    async def _create_folder(self, folder: str):
        """Создаёт папку, если её нет"""
        try:
            await self.client.put(
                self.resources_endpoint,
                headers=self.headers,
                params={"path": f"{YANDEX_DISK_PATH_PREFIX}{folder}"},
            )
        except httpx.HTTPStatusError as e:
            # Папка уже существует (код 409) — игнорируем
            if e.response.status_code != HTTPStatus.CONFLICT:
                raise


async def get_yandex_client():
    """Dependency для получения клиента Яндекс Диска"""

    if settings.yandex_disk_token is None:
        raise HTTPException(
            status_code=HTTPStatus.SERVICE_UNAVAILABLE,
            detail="Яндекс Диск не настроен. Пожалуйста, "
            "добавьте YANDEX_DISK_TOKEN в .env-файл",
        )

    async with YandexDiskClient(settings.yandex_disk_token) as client:
        yield client
