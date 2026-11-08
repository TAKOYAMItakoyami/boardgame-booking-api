from collections.abc import Sequence
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.constants import ReportKey
from app.crud.base import CRUDBase
from app.models import Booking, User


class CRUDBooking(CRUDBase):

    async def get_bookings_at_the_same_time(
        self,
        *,
        from_booking: datetime,
        to_booking: datetime,
        boardgame_id: int,
        booking_id: int | None = None,
        session: AsyncSession,
    ) -> Sequence[Booking]:
        statement = select(self.model).where(
            self.model.boardgame_id == boardgame_id,
            and_(
                from_booking < self.model.to_booking,
                to_booking > self.model.from_booking,
            ),
        )
        if booking_id is not None:
            statement = statement.where(self.model.id != booking_id)
        bookings = await session.execute(statement)
        return bookings.scalars().all()

    async def get_future_bookings_for_boardgame(
        self, boardgame_id: int, session: AsyncSession
    ) -> Sequence[Booking]:
        bookings = await session.execute(
            select(self.model).where(
                self.model.boardgame_id == boardgame_id,
                self.model.to_booking > datetime.now(),
            )
        )
        return bookings.scalars().all()

    async def get_by_user(
        self, user: User, session: AsyncSession
    ) -> Sequence[Booking]:
        bookings = await session.execute(
            select(self.model).where(self.model.user_id == user.id)
        )
        return bookings.scalars().all()

    async def get_bookings_for_report(
        self,
        from_date: datetime,
        to_date: datetime,
        session: AsyncSession,
    ) -> list[dict[str, Any]]:
        """
        Получение агрегированной статистики по играм за период.
        Поддержка SQLite и Postgres.
        """
        statement = (
            select(self.model)
            .where(
                self.model.from_booking >= from_date,
                self.model.to_booking <= to_date,
            )
            .options(selectinload(self.model.boardgame))
        )
        result = await session.execute(statement)
        bookings = result.scalars().all()

        if not bookings:
            return []

        stats: dict[int, dict[str, Any]] = {}
        for booking in bookings:
            bg_id = booking.boardgame_id

            if bg_id not in stats:
                stats[bg_id] = {
                    ReportKey.NAME: booking.boardgame.name,
                    ReportKey.BOOKINGS_COUNT: 0,
                    ReportKey.BOOKING_TIME: timedelta(0),
                    ReportKey.PLAYERS_COUNT_MIN: booking.players_count,
                    ReportKey.PLAYERS_COUNT_MAX: booking.players_count,
                }

            game_stats = stats[bg_id]
            game_stats[ReportKey.BOOKINGS_COUNT] += 1
            game_stats[ReportKey.BOOKING_TIME] += (
                booking.to_booking - booking.from_booking
            )
            game_stats[ReportKey.PLAYERS_COUNT_MIN] = min(
                game_stats[ReportKey.PLAYERS_COUNT_MIN], booking.players_count
            )
            game_stats[ReportKey.PLAYERS_COUNT_MAX] = max(
                game_stats[ReportKey.PLAYERS_COUNT_MAX], booking.players_count
            )

        return list(stats.values())


booking_crud = CRUDBooking(Booking)
