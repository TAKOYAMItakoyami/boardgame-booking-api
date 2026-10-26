from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User


class CRUDBase:

    def __init__(self, model):
        self.model = model

    async def get(
        self,
        obj_id: int,
        session: AsyncSession,
    ):
        db_obj = await session.execute(
            select(self.model).where(self.model.id == obj_id)
        )
        return db_obj.scalars().first()

    async def get_multi(self, session, skip: int = 0, limit: int = 100):
        db_objs = await session.execute(
            select(self.model).offset(skip).limit(limit)
        )
        return db_objs.scalars().all()

    async def create(
        self, obj_in, session: AsyncSession, user: User | None = None
    ):
        obj_in_data = obj_in.model_dump()
        if user is not None:
            obj_in_data["user_id"] = user.id
        db_obj = self.model(**obj_in_data)
        session.add(db_obj)
        await session.commit()
        await session.refresh(db_obj)
        return db_obj

    async def update(
        self,
        db_obj,
        obj_in,
        session: AsyncSession,
    ):
        valid = set(self.model.__table__.columns.keys())
        update_data = obj_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if field in valid:
                setattr(db_obj, field, value)
        session.add(db_obj)
        await session.commit()
        await session.refresh(db_obj)
        return db_obj

    async def remove(
        self,
        db_obj,
        session: AsyncSession,
    ):
        await session.delete(db_obj)
        await session.commit()
        return db_obj
