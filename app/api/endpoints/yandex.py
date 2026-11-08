import logging
from datetime import datetime, timedelta
from http import HTTPStatus

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import REPORT_PERIOD_DAYS, REPORTS_FOLDER_DEFAULT
from app.core.db import get_async_session
from app.core.user import current_superuser
from app.core.yandex_client import YandexDiskClient, get_yandex_client
from app.crud.booking import booking_crud
from app.services.yandex_api import create_simple_report, set_user_permissions

router = APIRouter()

logger = logging.getLogger(__name__)


@router.post(
    "/",
    response_model=str,
    dependencies=[Depends(current_superuser)],
    summary="Создать Excel-отчёт на Яндекс Диске",
    description=f"""
    Создаёт Excel-файл с отчётом по бронированию настольных игр.
    Файл сохраняется на Яндекс Диске в папке {REPORTS_FOLDER_DEFAULT}
    и становится доступен по публичной ссылке.

    Только для администратора антикафе.
    """,
)
async def get_report(
    session: AsyncSession = Depends(get_async_session),
    yandex_client: YandexDiskClient = Depends(get_yandex_client),
) -> str:
    """
    Создание отчёта в Excel-файле на Яндекс Диске
    """
    to_date = datetime.now()
    from_date = to_date - timedelta(days=REPORT_PERIOD_DAYS)
    bookings = await booking_crud.get_bookings_for_report(
        from_date=from_date, to_date=to_date, session=session
    )

    if not bookings:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail="Нет данных для формирования отчёта",
        )

    try:
        file_path = await create_simple_report(bookings, yandex_client)
        public_url = await set_user_permissions(file_path, yandex_client)

        return public_url
    except Exception:
        logger.exception("Критическая ошибка при создании отчета")
        raise HTTPException(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            detail="Внутренняя ошибка сервера при формировании отчета.",
        )
