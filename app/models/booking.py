from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base, CommonMixin

if TYPE_CHECKING:
    from app.models.boardgame import Boardgame
    from app.models.user import User


class Booking(CommonMixin, Base):
    from_booking: Mapped[datetime] = mapped_column(DateTime)
    to_booking: Mapped[datetime] = mapped_column(DateTime)
    youngest_player_age: Mapped[int] = mapped_column(Integer, nullable=False)
    players_count: Mapped[int] = mapped_column(Integer, nullable=False)

    boardgame_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("boardgame.id", name="fk_booking_boardgame_id_boardgame"),
    )
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("user.id", name="fk_booking_user_id_user")
    )

    boardgame: Mapped["Boardgame"] = relationship(
        back_populates="bookings",
    )
    user: Mapped["User"] = relationship(
        back_populates="bookings",
    )

    def __repr__(self):
        return (
            f"Забронировано с {self.from_booking} "
            f"по {self.to_booking} "
            f"на {self.players_count} человек"
        )
