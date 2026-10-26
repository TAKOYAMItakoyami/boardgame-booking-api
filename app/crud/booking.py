from collections.abc import Sequence
from datetime import datetime

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

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


booking_crud = CRUDBooking(Booking)
