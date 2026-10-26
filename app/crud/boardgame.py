from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.base import CRUDBase
from app.models.boardgame import Boardgame


class CRUDBoardgame(CRUDBase):

    async def get_available(
        self, session: AsyncSession
    ) -> Sequence[Boardgame]:
        """Возвращает только игры, доступные для бронирования."""
        result = await session.execute(
            select(self.model).where(self.model.is_available.is_(True))
        )
        return result.scalars().all()

    async def get_boardgame_id_by_name(
        self,
        boardgame_name: str,
        session: AsyncSession,
    ) -> int | None:
        result = await session.execute(
            select(self.model.id).where(self.model.name == boardgame_name)
        )
        db_boardgame_id = result.scalars().first()
        return db_boardgame_id


boardgame_crud = CRUDBoardgame(Boardgame)
