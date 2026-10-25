from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator
)

from app.core.constants import (
    BOARDGAME_NAME_MIN_LENGTH,
    BOARDGAME_NAME_MAX_LENGTH,
    BOARDGAME_DESCRIPTION_MAX_LENGTH,
    PLAYERS_LIMIT_MAX,
    PLAYERS_MIN,
    AGE_MIN,
    PLAYTIME_MINUTES_MIN
)


class BoardGameBase(BaseModel):
    name: str | None = Field(
        None,
        min_length=BOARDGAME_NAME_MIN_LENGTH,
        max_length=BOARDGAME_NAME_MAX_LENGTH
    )
    description: str | None = Field(
        None,
        max_length=BOARDGAME_DESCRIPTION_MAX_LENGTH
    )
    max_players: int | None = Field(None, ge=PLAYERS_MIN, le=PLAYERS_LIMIT_MAX)
    min_players: int | None = Field(None, ge=PLAYERS_MIN)
    min_age: int | None = Field(None, ge=AGE_MIN)
    playtime_minutes: int | None = Field(None, ge=PLAYTIME_MINUTES_MIN)
    is_available: bool | None = None

    @field_validator('name', mode='before')
    @classmethod
    def strip_name(cls, value: str | None) -> str | None:
        if isinstance(value, str):
            return value.strip()
        return value

    @field_validator('description', mode='before')
    @classmethod
    def strip_description(cls, value: str | None) -> str | None:
        if isinstance(value, str):
            value = value.strip()
            return value or None
        return value


class BoardGameCreate(BoardGameBase):
    name: str = Field(
        ...,
        min_length=BOARDGAME_NAME_MIN_LENGTH,
        max_length=BOARDGAME_NAME_MAX_LENGTH
    )
    max_players: int = Field(..., ge=PLAYERS_MIN, le=PLAYERS_LIMIT_MAX)
    min_players: int = Field(..., ge=PLAYERS_MIN)
    min_age: int = Field(..., ge=AGE_MIN)
    playtime_minutes: int = Field(..., ge=PLAYTIME_MINUTES_MIN)
    is_available: bool = Field(default=True)

    @model_validator(mode='after')
    def check_players_range(self):
        if self.min_players > self.max_players:
            raise ValueError('min_players не может быть больше max_players')
        return self


class BoardGameUpdate(BoardGameBase):
    @field_validator(
        'name', 'max_players', 'min_players',
        'min_age', 'playtime_minutes', 'is_available',
    )
    @classmethod
    def cannot_be_null(cls, value, info):
        if value is None:
            raise ValueError(f'Поле {info.field_name} не может быть пустым!')
        return value

    @model_validator(mode='after')
    def check_min_max_players(self):
        if self.min_players is not None and self.max_players is not None:
            if self.min_players > self.max_players:
                raise ValueError(
                    'min_players не может быть больше max_players'
                )
        return self


class BoardGameDB(BaseModel):
    id: int
    name: str
    description: str | None
    max_players: int
    min_players: int
    min_age: int
    playtime_minutes: int
    is_available: bool

    model_config = ConfigDict(from_attributes=True)