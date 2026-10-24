from fastapi import APIRouter

from app.api.endpoints import (
    # boardgame_router,
    # booking_router,
    user_router,
)

main_router = APIRouter()
# main_router.include_router(
#     boardgame_router,
#     prefix="/boardgame",
#     tags=["boardgames"],
# )
# main_router.include_router(
#     booking_router,
#     prefix="/booking",
#     tags=["bookings"],
# )

main_router.include_router(user_router)
