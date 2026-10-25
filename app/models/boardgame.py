from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.constants import (
    BOARDGAME_DESCRIPTION_MAX_LENGTH,
    BOARDGAME_NAME_MAX_LENGTH
)
from app.core.db import Base, CommonMixin


class Boardgame(CommonMixin, Base):
    name: Mapped[str] = mapped_column(
        String(BOARDGAME_NAME_MAX_LENGTH),
        unique=True,
        nullable=False
    )
    description: Mapped[str | None] = mapped_column(
        String(BOARDGAME_DESCRIPTION_MAX_LENGTH),
        nullable=True
    )
    max_players: Mapped[int] = mapped_column(nullable=False)
    min_players: Mapped[int] = mapped_column(nullable=False)
    min_age: Mapped[int] = mapped_column(nullable=False)
    playtime_minutes: Mapped[int] = mapped_column(nullable=False)
    is_available: Mapped[bool] = mapped_column(default=True, nullable=False)

    bookings: Mapped[list["Booking"]] = relationship(
        back_populates="boardgame",
    )

    def __repr__(self):
        return f'<Настольная игра {self.name}>'
