from datetime import datetime

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    NaiveDatetime,
    field_validator,
    model_validator,
)
from typing_extensions import Self

from app.core.constants import (
    AGE_MIN,
    FROM_TIME,
    ID_MIN,
    PLAYERS_LIMIT_MAX,
    PLAYERS_MIN,
    TO_TIME,
)


class BookingBase(BaseModel):
    from_booking: NaiveDatetime | None = Field(None, examples=[FROM_TIME])
    to_booking: NaiveDatetime | None = Field(None, examples=[TO_TIME])
    youngest_player_age: int | None = Field(None, ge=AGE_MIN)
    players_count: int | None = Field(
        None, ge=PLAYERS_MIN, le=PLAYERS_LIMIT_MAX
    )

    model_config = ConfigDict(extra="forbid")


class BookingUpdate(BookingBase):
    @model_validator(mode="before")
    @classmethod
    def check_from_to_booking(cls, data):
        if isinstance(data, dict):
            has_from = "from_booking" in data
            has_to = "to_booking" in data

            if has_from != has_to:
                raise ValueError(
                    "from_booking и to_booking должны быть переданы вместе"
                )
            if has_from:
                if data["from_booking"] is None:
                    raise ValueError("from_booking не может быть null")
                if data["to_booking"] is None:
                    raise ValueError("to_booking не может быть null")
        return data

    @field_validator("from_booking")
    @classmethod
    def check_from_booking_later_than_now(cls, value):
        if value <= datetime.now():
            error = (
                "Время начала бронирования настольной игры"
                "не может быть меньше текущего времени"
            )
            raise ValueError(error)
        return value

    @model_validator(mode="after")
    def check_from_booking_before_to_booking(self) -> Self:
        if self.from_booking is not None and self.to_booking is not None:
            if self.from_booking >= self.to_booking:
                error = (
                    "Время начала бронирования настольной игры"
                    "не может быть больше времени окончания"
                )
                raise ValueError(error)
        return self


class BookingCreate(BookingUpdate):
    from_booking: NaiveDatetime = Field(..., examples=[FROM_TIME])
    to_booking: NaiveDatetime = Field(..., examples=[TO_TIME])
    youngest_player_age: int = Field(..., ge=AGE_MIN)
    players_count: int = Field(..., ge=PLAYERS_MIN, le=PLAYERS_LIMIT_MAX)

    boardgame_id: int = Field(..., ge=ID_MIN)


class BookingDB(BaseModel):
    id: int
    from_booking: datetime
    to_booking: datetime
    youngest_player_age: int
    players_count: int

    boardgame_id: int
    user_id: int

    model_config = ConfigDict(from_attributes=True)
