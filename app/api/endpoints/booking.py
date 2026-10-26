from http import HTTPStatus
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.validators import (
    check_booking_before_create,
    check_booking_before_delete,
    check_booking_before_edit,
    check_bookings_intersections,
)
from app.core.db import get_async_session
from app.core.user import current_superuser, current_user
from app.crud.booking import booking_crud
from app.models import User
from app.schemas.booking import BookingCreate, BookingDB, BookingUpdate

router = APIRouter()
SessionDep = Annotated[AsyncSession, Depends(get_async_session)]


@router.post("/", response_model=BookingDB, status_code=HTTPStatus.CREATED)
async def create_booking(
    booking_in: BookingCreate,
    session: SessionDep,
    user: Annotated[User, Depends(current_user)],
):
    await check_booking_before_create(booking_in, session)
    await check_bookings_intersections(
        from_booking=booking_in.from_booking,
        to_booking=booking_in.to_booking,
        boardgame_id=booking_in.boardgame_id,
        session=session,
    )
    new_booking = await booking_crud.create(booking_in, session, user)
    return new_booking


@router.get(
    "/",
    response_model=list[BookingDB],
    dependencies=[Depends(current_superuser)],
)
async def get_all_bookings(
    session: SessionDep,
):
    """Только для администратора антикафе."""
    return await booking_crud.get_multi(session)


@router.delete("/{booking_id}", response_model=BookingDB)
async def remove_booking(
    booking_id: int,
    session: SessionDep,
    user: Annotated[User, Depends(current_user)],
):
    """Для администратора антикафе или создателей объекта бронирования."""
    booking = await check_booking_before_delete(booking_id, session, user)
    return await booking_crud.remove(booking, session)


@router.patch("/{booking_id}", response_model=BookingDB)
async def update_booking(
    booking_id: int,
    booking_in: BookingUpdate,
    session: SessionDep,
    user: Annotated[User, Depends(current_user)],
):
    """Для администратора антикафе или создателей объекта бронирования."""
    booking = await check_booking_before_edit(
        booking_id, booking_in, session, user
    )
    return await booking_crud.update(
        db_obj=booking,
        obj_in=booking_in,
        session=session,
    )


@router.get(
    "/my_bookings",
    response_model=list[BookingDB],
    response_model_exclude={"__all__": {"user_id"}},
)
async def get_my_bookings(
    session: SessionDep, user: Annotated[User, Depends(current_user)]
):
    """Получает список всех бронирований для текущего пользователя."""
    return await booking_crud.get_by_user(user=user, session=session)
