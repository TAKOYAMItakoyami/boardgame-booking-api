from fastapi import APIRouter

from app.api.endpoints import (
    boardgame_router,
    booking_router,
    user_router,
    yandex_router,
)

main_router = APIRouter()
main_router.include_router(
    boardgame_router,
    prefix="/boardgames",
    tags=["boardgames"],
)
main_router.include_router(
    booking_router,
    prefix="/bookings",
    tags=["bookings"],
)
main_router.include_router(
    yandex_router, prefix="/yandex", tags=["Yandex Disk"]
)
main_router.include_router(user_router)
