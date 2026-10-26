from http import HTTPStatus
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.validators import (
    check_boardgame_exists,
    check_name_boardgame_duplicate,
)
from app.core.db import get_async_session
from app.core.user import current_superuser, optional_current_user
from app.crud.boardgame import boardgame_crud
from app.crud.booking import booking_crud
from app.models.user import User
from app.schemas.boardgame import BoardgameCreate, BoardgameDB, BoardgameUpdate
from app.schemas.booking import BookingDB

router = APIRouter()

SessionDep = Annotated[AsyncSession, Depends(get_async_session)]


@router.post(
    "/",
    response_model=BoardgameDB,
    response_model_exclude_none=True,
    dependencies=[Depends(current_superuser)],
    status_code=HTTPStatus.CREATED,
)
async def create_new_boardgame(
    boardgame: BoardgameCreate,
    session: SessionDep,
):
    """Только для администратора антикафе."""
    await check_name_boardgame_duplicate(boardgame.name, session)
    return await boardgame_crud.create(boardgame, session)


@router.get(
    "/", response_model=list[BoardgameDB], response_model_exclude_none=True
)
async def get_all_boardgames(
    session: SessionDep,
    user: Annotated[User | None, Depends(optional_current_user)],
):
    """Администратор видит все игры, остальные — только доступные."""
    if user and user.is_superuser:
        return await boardgame_crud.get_multi(session)
    return await boardgame_crud.get_available(session)


@router.patch(
    "/{boardgame_id}",
    response_model=BoardgameDB,
    response_model_exclude_none=True,
    dependencies=[Depends(current_superuser)],
)
async def partially_update_boardgame(
    boardgame_id: int,
    obj_in: BoardgameUpdate,
    session: SessionDep,
):
    """Только для администратора антикафе."""
    boardgame = await check_boardgame_exists(boardgame_id, session)
    if obj_in.name is not None:
        await check_name_boardgame_duplicate(
            obj_in.name, session, boardgame_id=boardgame.id
        )
    return await boardgame_crud.update(boardgame, obj_in, session)


@router.delete(
    "/{boardgame_id}",
    response_model=BoardgameDB,
    response_model_exclude_none=True,
    dependencies=[Depends(current_superuser)],
)
async def remove_boardgame(
    boardgame_id: int,
    session: SessionDep,
):
    """Только для администратора антикафе."""
    boardgame = await check_boardgame_exists(boardgame_id, session)
    return await boardgame_crud.remove(boardgame, session)


@router.get(
    "/{boardgame_id}/bookings",
    response_model=list[BookingDB],
    response_model_exclude={"__all__": {"user_id"}},
)
async def get_bookings_for_boardgame(
    boardgame_id: int,
    session: SessionDep,
):
    """Посмотреть бронирования конкретной игры."""
    await check_boardgame_exists(boardgame_id, session)
    return await booking_crud.get_future_bookings_for_boardgame(
        boardgame_id=boardgame_id, session=session
    )
