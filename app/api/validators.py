from datetime import datetime
from http import HTTPStatus

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.boardgame import boardgame_crud
from app.crud.booking import booking_crud
from app.models import Boardgame, Booking, User
from app.schemas.booking import BookingCreate, BookingUpdate


async def check_booking_rules(
    boardgame: Boardgame, players_count: int, youngest_player_age: int
) -> None:
    """Проверяет бизнес-правила бронирования для конкретной игры."""
    if not boardgame.is_available:
        raise HTTPException(
            status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
            detail="Настольная игра недоступна для бронирования!",
        )

    if not (boardgame.min_players <= players_count <= boardgame.max_players):
        raise HTTPException(
            status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
            detail=(
                "players_count вне диапазона игры "
                f"({boardgame.min_players}-{boardgame.max_players})"
            ),
        )

    if youngest_player_age < boardgame.min_age:
        raise HTTPException(
            status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
            detail=(
                f"youngest_player_age не может быть меньше {boardgame.min_age}"
            ),
        )


async def check_name_boardgame_duplicate(
    boardgame_name: str, session: AsyncSession, boardgame_id: int | None = None
) -> None:
    existing_id = await boardgame_crud.get_boardgame_id_by_name(
        boardgame_name, session
    )
    if existing_id is not None and existing_id != boardgame_id:
        raise HTTPException(
            status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
            detail="Настольная игра с таким именем уже существует!",
        )


async def check_boardgame_exists(
    boardgame_id: int,
    session: AsyncSession,
) -> Boardgame:
    boardgame = await boardgame_crud.get(boardgame_id, session)
    if boardgame is None:
        raise HTTPException(
            status_code=404, detail="Настольная игра не найдена!"
        )
    return boardgame


async def check_booking_before_create(
    booking_in: BookingCreate, session: AsyncSession
) -> Boardgame:
    boardgame = await check_boardgame_exists(booking_in.boardgame_id, session)
    await check_booking_rules(
        boardgame=boardgame,
        players_count=booking_in.players_count,
        youngest_player_age=booking_in.youngest_player_age,
    )
    return boardgame


async def check_bookings_intersections(
    *,
    from_booking: datetime,
    to_booking: datetime,
    boardgame_id: int,
    booking_id: int | None = None,
    session: AsyncSession,
) -> None:
    bookings = await booking_crud.get_bookings_at_the_same_time(
        from_booking=from_booking,
        to_booking=to_booking,
        boardgame_id=boardgame_id,
        booking_id=booking_id,
        session=session,
    )
    if bookings:
        conflicts = [
            {
                "from_booking": booking.from_booking.isoformat(),
                "to_booking": booking.to_booking.isoformat(),
            }
            for booking in bookings
        ]
        raise HTTPException(
            status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
            detail={
                "message": "Игра уже забронирована на это время",
                "conflicts": conflicts,
            },
        )


async def check_booking_before_edit(
    booking_id: int,
    booking_in: BookingUpdate,
    session: AsyncSession,
    user: User,
) -> Booking:
    booking = await booking_crud.get(obj_id=booking_id, session=session)
    if booking is None:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail="Бронь не найдена!"
        )
    if booking.user_id != user.id and not user.is_superuser:
        raise HTTPException(
            status_code=HTTPStatus.FORBIDDEN,
            detail="Невозможно отредактировать чужую бронь!",
        )
    boardgame = await check_boardgame_exists(booking.boardgame_id, session)
    players_count = (
        booking_in.players_count
        if booking_in.players_count is not None
        else booking.players_count
    )
    youngest_player_age = (
        booking_in.youngest_player_age
        if booking_in.youngest_player_age is not None
        else booking.youngest_player_age
    )
    await check_booking_rules(
        boardgame=boardgame,
        players_count=players_count,
        youngest_player_age=youngest_player_age,
    )
    if (
        booking_in.from_booking is not None
        and booking_in.to_booking is not None
    ):
        await check_bookings_intersections(
            from_booking=booking_in.from_booking,
            to_booking=booking_in.to_booking,
            boardgame_id=booking.boardgame_id,
            booking_id=booking.id,
            session=session,
        )
    return booking


async def check_booking_before_delete(
    booking_id: int, session: AsyncSession, user: User
) -> Booking:
    booking = await booking_crud.get(obj_id=booking_id, session=session)
    if booking is None:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail="Бронь не найдена!"
        )
    if booking.user_id != user.id and not user.is_superuser:
        raise HTTPException(
            status_code=HTTPStatus.FORBIDDEN,
            detail="Невозможно удалить чужую бронь!",
        )
    return booking
