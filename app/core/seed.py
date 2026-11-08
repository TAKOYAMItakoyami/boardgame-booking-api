import asyncio
import random
from datetime import datetime, timedelta

from faker import Faker
from sqlalchemy import select

from app.core.config import settings
from app.core.db import AsyncSessionLocal
from app.models import Boardgame, Booking, User

fake = Faker("ru_RU")

# --- Константы для генерации ---
GAMES_TO_CREATE = 10
BOOKINGS_TO_CREATE = 15

# Параметры для игр
MIN_PLAYERS_RANGE = (1, 3)
MAX_PLAYERS_RANGE = (4, 8)
AGES_CHOICES = [0, 6, 12, 18]
PLAYTIME_CHOICES = [30, 45, 60, 90, 120]
DESCRIPTION_MAX_LENGTH = 200

# Параметры для броней
BOOKING_DAYS_AHEAD = (1, 5)
BOOKING_HOURS_AHEAD = (1, 10)
YOUNGEST_AGE_RANGE = (18, 30)


async def seed_data():
    """Наполняет базу тестовыми играми и бронями."""
    async with AsyncSessionLocal() as session:
        user_result = await session.execute(
            select(User).where(User.email == settings.first_superuser_email)
        )
        user = user_result.scalars().first()
        if not user:
            print("Суперюзер не найден! Сначала запусти приложение.")
            return

        boardgames = []
        for _ in range(GAMES_TO_CREATE):
            game = Boardgame(
                name=fake.unique.word().capitalize(),
                description=fake.text(max_nb_chars=DESCRIPTION_MAX_LENGTH),
                min_players=random.randint(*MIN_PLAYERS_RANGE),
                max_players=random.randint(*MAX_PLAYERS_RANGE),
                min_age=random.choice(AGES_CHOICES),
                playtime_minutes=random.choice(PLAYTIME_CHOICES),
                is_available=True,
            )
            session.add(game)
            boardgames.append(game)

        await session.flush()
        print(f"Создано {len(boardgames)} настольных игр.")

        now = datetime.now()
        for _ in range(BOOKINGS_TO_CREATE):
            game = random.choice(boardgames)

            start_time = now - timedelta(
                days=random.randint(*BOOKING_DAYS_AHEAD),
                hours=random.randint(*BOOKING_HOURS_AHEAD),
            )
            end_time = start_time + timedelta(minutes=game.playtime_minutes)

            booking = Booking(
                from_booking=start_time,
                to_booking=end_time,
                youngest_player_age=random.randint(*YOUNGEST_AGE_RANGE),
                players_count=random.randint(
                    game.min_players, game.max_players
                ),
                boardgame_id=game.id,
                user_id=user.id,
            )
            session.add(booking)

        await session.commit()
        print(f"Создано {BOOKINGS_TO_CREATE} тестовых бронирований.")
        print("База данных успешно наполнена!")


if __name__ == "__main__":
    asyncio.run(seed_data())
