from typing import Annotated

from fastapi import Depends, Request
from fastapi_users import (
    BaseUserManager,
    FastAPIUsers,
    IntegerIDMixin,
    InvalidPasswordException,
    schemas,
)
from fastapi_users.authentication import (
    AuthenticationBackend,
    BearerTransport,
    JWTStrategy,
)
from fastapi_users_db_sqlalchemy import SQLAlchemyUserDatabase
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.constants import JWT_LIFETIME, MIN_LEN_PASSWORD
from app.core.db import get_async_session
from app.models.user import User


async def get_user_db(
    session: Annotated[AsyncSession, Depends(get_async_session)],
):
    yield SQLAlchemyUserDatabase(session, User)


bearer_transport = BearerTransport(tokenUrl="auth/jwt/login")


def get_jwt_strategy() -> JWTStrategy:
    return JWTStrategy(secret=settings.secret, lifetime_seconds=JWT_LIFETIME)


auth_backend = AuthenticationBackend(
    name="jwt",
    transport=bearer_transport,
    get_strategy=get_jwt_strategy,
)


class UserManager(IntegerIDMixin, BaseUserManager[User, int]):

    async def validate_password(
        self,
        password: str,
        user: schemas.BaseUserCreate | User,
    ) -> None:
        if len(password) < MIN_LEN_PASSWORD:
            error = (
                f"Пароль должен содержать не менее {MIN_LEN_PASSWORD} символов"
            )
            raise InvalidPasswordException(reason=error)
        if user.email in password:
            error = "Пароль не может содержать ваш email"
            raise InvalidPasswordException(reason=error)

    async def on_after_register(
        self, user: User, request: Request | None = None
    ):
        print(f"Пользователь {user.email} зарегистрирован.")


async def get_user_manager(user_db=Depends(get_user_db)):
    yield UserManager(user_db)


fastapi_users = FastAPIUsers[User, int](
    get_user_manager,
    [auth_backend],
)

current_user = fastapi_users.current_user(active=True)
current_superuser = fastapi_users.current_user(active=True, superuser=True)
optional_current_user = fastapi_users.current_user(optional=True)
