# Boardgame Booking API

Проект на Python с использованием FastAPI, асинхронного программирования и SQLAlchemy 2.0.

REST API для бронирования настольных игр антикафе **Host&Хвост**.

Приложение работает с SQLite при локальной разработке и с PostgreSQL в Docker,
переключение — одной переменной окружения. Запуск приложения — через `uvicorn`
напрямую или через `docker compose`.

## Описание

**Boardgame Booking API** — сервис, который позволяет:

- вести каталог настольных игр: добавлять, обновлять, скрывать из бронирования;
- бронировать игру на конкретный интервал времени;
- автоматически отсекать пересекающиеся бронирования по одной игре;
- проверять бронь на соответствие правилам игры (число игроков, минимальный возраст);
- видеть свои бронирования и все будущие брони выбранной игры;
- регистрироваться и аутентифицироваться по JWT-токену.

### Основные сущности

| Сущность    | Описание                                                                                                              |
| ----------- | --------------------------------------------------------------------------------------------------------------------- |
| `Boardgame` | Настольная игра (название, описание, `min_players`/`max_players`, `min_age`, `playtime_minutes`, `is_available`)      |
| `Booking`   | Бронирование (интервал `from_booking`/`to_booking`, `players_count`, `youngest_player_age`, привязка к игре и автору) |
| `User`      | Пользователь системы (email, хеш пароля, флаг суперюзера)                                                              |

Связи: `Boardgame 1 — N Booking`, `User 1 — N Booking`.

### Бизнес-правила

**Настольные игры**

- название уникально (2–100 символов), при дубликате — `422`;
- `min_players` не может быть больше `max_players`;
- обычным пользователям и гостям доступны только игры с `is_available = true`, администратор видит все игры.

**Бронирования**

- `from_booking` не может быть в прошлом, `from_booking < to_booking`;
- `players_count` должен попадать в диапазон `min_players…max_players` игры;
- `youngest_player_age` не может быть меньше `min_age` игры;
- игра не может быть забронирована на пересекающийся интервал — сервис возвращает список конфликтов;
- изменить или удалить бронь может только её автор либо администратор (`403` иначе).

## Возможности API

### Настольные игры

| Метод    | Путь                                | Описание                                                  | Доступ              |
| -------- | ----------------------------------- | --------------------------------------------------------- | ------------------- |
| `POST`   | `/boardgames/`                      | Создать игру                                               | Суперюзер           |
| `GET`    | `/boardgames/`                      | Список игр (суперюзер — все, остальные — доступные)         | Все                 |
| `PATCH`  | `/boardgames/{boardgame_id}`        | Частично обновить игру                                     | Суперюзер           |
| `DELETE` | `/boardgames/{boardgame_id}`        | Удалить игру                                               | Суперюзер           |
| `GET`    | `/boardgames/{boardgame_id}/bookings` | Будущие бронирования конкретной игры                       | Все (без `user_id`) |

### Бронирования

| Метод    | Путь                      | Описание                       | Доступ                       |
| -------- | ------------------------- | ------------------------------ | ---------------------------- |
| `POST`   | `/bookings/`              | Создать бронирование           | Авторизован                  |
| `GET`    | `/bookings/`              | Список всех бронирований       | Суперюзер                    |
| `GET`    | `/bookings/my_bookings`   | Список своих бронирований      | Авторизован                  |
| `PATCH`  | `/bookings/{booking_id}`  | Частично обновить бронирование | Автор брони или суперюзер    |
| `DELETE` | `/bookings/{booking_id}`  | Удалить бронирование           | Автор брони или суперюзер    |

### Аутентификация и пользователи

| Метод   | Путь               | Описание                                       |
| ------- | ------------------ | ---------------------------------------------- |
| `POST`  | `/auth/register`   | Регистрация нового пользователя (`201`)        |
| `POST`  | `/auth/jwt/login`  | Вход по email и паролю, возвращает JWT         |
| `POST`  | `/auth/jwt/logout` | Выход (завершение сессии)                      |
| `GET`   | `/users/me`        | Данные текущего пользователя                   |
| `PATCH` | `/users/me`        | Частично обновить данные текущего пользователя |
| `GET`   | `/users/{id}`      | Данные пользователя по id                      |
| `PATCH` | `/users/{id}`      | Частично обновить данные пользователя          |

Удаление пользователей (`DELETE /users/{id}`) в API сознательно отключено.

Требования к паролю: не короче 8 символов и не содержит email пользователя.

Интерактивная документация доступна после запуска (порт зависит от способа запуска):

| Режим | Swagger UI | ReDoc |
| ----- | ---------- | ----- |
| Локальный запуск (`uvicorn`) | `http://127.0.0.1:8000/docs` | `http://127.0.0.1:8000/redoc` |
| Запуск в Docker (`docker compose`) | `http://127.0.0.1:8080/docs` | `http://127.0.0.1:8080/redoc` |

## База данных

Проект поддерживает две СУБД — выбор делается одной переменной `DATABASE_URL`
в файле `.env`, код приложения от этого не зависит:

| Режим | СУБД | `DATABASE_URL` |
| ----- | ---- | -------------- |
| Локальная разработка | SQLite | `sqlite+aiosqlite:///./bgbooking.db` |
| Docker / прод | PostgreSQL 16 | `postgresql+asyncpg://<user>:<password>@db:5432/<db>` |

Обе схемы подключаются через async-движок SQLAlchemy 2.0 (`aiosqlite` и
`asyncpg`), поэтому `alembic` и все CRUD-запросы работают одинаково с любой БД.

## Установка

### Требования

- Python 3.12
- pip
- Docker и Docker Compose (только для варианта с PostgreSQL)

### 1. Клонирование и переменные окружения

```bash
git clone git@github.com:TAKOYAMItakoyami/boardgame-booking-api.git
cd boardgame-booking-api
```

Создайте файл `.env` из готового шаблона:

```bash
cp .env.example .env
```

В `.env.example` оба варианта `DATABASE_URL` уже описаны — для SQLite и для
PostgreSQL. Активна та строка, которая не закомментирована:

```env
# Вариант 1: Docker + PostgreSQL (хост db — имя сервиса из docker-compose.yml)
DATABASE_URL=postgresql+asyncpg://user:password@db:5432/booking

# Вариант 2: локальная разработка на SQLite
# DATABASE_URL=sqlite+aiosqlite:///./bgbooking.db

# Реквизиты контейнера PostgreSQL (нужны только для Docker)
POSTGRES_USER=user
POSTGRES_PASSWORD=password
POSTGRES_DB=booking
```

| Переменная                 | Назначение                                     |
| -------------------------- | ---------------------------------------------- |
| `APP_TITLE`                | Название сервиса в OpenAPI-документации        |
| `DESCRIPTION`              | Описание сервиса в OpenAPI-документации        |
| `SECRET`                   | Секретный ключ для подписи JWT-токенов         |
| `DATABASE_URL`             | Строка подключения async-движка SQLAlchemy     |
| `FIRST_SUPERUSER_EMAIL`    | Email первого администратора                   |
| `FIRST_SUPERUSER_PASSWORD` | Пароль первого администратора                  |
| `POSTGRES_USER`            | Пользователь контейнера PostgreSQL              |
| `POSTGRES_PASSWORD`        | Пароль контейнера PostgreSQL                    |
| `POSTGRES_DB`              | Имя базы контейнера PostgreSQL                  |

Значения `POSTGRES_USER` / `POSTGRES_PASSWORD` / `POSTGRES_DB` должны совпадать
с сегментом `<user>:<password>@db:5432/<db>` в `DATABASE_URL`.

Файл `.env` в репозиторий не попадает (добавлен в `.gitignore`), поэтому
`cp .env.example .env` — обязательный шаг после клонирования.

### 2a. Локальный запуск (SQLite)

1. В `.env` закомментируйте строку `DATABASE_URL` с `postgresql+asyncpg` и
   раскомментируйте строку с `sqlite+aiosqlite`.

2. Создайте и активируйте виртуальное окружение:

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux / macOS
source venv/bin/activate
```

3. Установите зависимости (прикладные + инструменты проверки кода и SQLite):

```bash
pip install -r requirements-dev.txt
```

4. Примените миграции:

```bash
alembic upgrade head
```

5. Запустите сервер разработки:

```bash
uvicorn app.main:app --reload
```

Сервер доступен по адресу `http://127.0.0.1:8000`, база — в файле
`bgbooking.db` в корне проекта.

### 2b. Запуск в Docker (PostgreSQL)

1. В `.env` оставьте активной строку `DATABASE_URL` с `postgresql+asyncpg`
   (хост — `db`, имя сервиса из `docker-compose.yml`) и заполните `POSTGRES_*`.

2. Соберите образ и поднимите контейнеры:

```bash
docker compose up --build -d
```

3. Проверьте, что сервисы поднялись:

```bash
docker compose ps
```

Приложение будет доступно по адресу `http://127.0.0.1:8080` (проброс
`8080:8000`), Swagger UI — `http://127.0.0.1:8080/docs`.

Остальные команды:

```bash
# Логи приложения
docker compose logs -f backend

# Остановить контейнеры (данные PostgreSQL останутся в volume pg_data)
docker compose down

# Остановить и удалить volume с данными
docker compose down -v
```

### Как устроен запуск в Docker

`docker-compose.yml` описывает два сервиса:

| Сервис    | Образ                | Что делает                                                                 |
| --------- | -------------------- | -------------------------------------------------------------------------- |
| `db`      | `postgres:16`        | PostgreSQL; данные в именованном volume `pg_data`; healthcheck `pg_isready` |
| `backend` | сборка из `Dockerfile` | FastAPI + uvicorn на порту 8000 внутри контейнера                          |

`backend` стартует только после того, как `db` станет healthy, и перед запуском
сервера сам применяет миграции:

```yaml
command: sh -c "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"
```

Поэтому отдельный шаг `alembic upgrade head` в Docker не нужен.

При старте приложения (в `lifespan`) автоматически создаётся первый суперюзер из
`FIRST_SUPERUSER_EMAIL` / `FIRST_SUPERUSER_PASSWORD`, если он ещё не существует.
Без этих переменных сервис работает, но администратор будет недоступен — игры
нельзя создать через API.

## Использование

> **Важно:** примеры ниже используют адрес `http://127.0.0.1:8000`. Если вы
> запустили приложение в Docker, замените порт на `8080`:
> `http://127.0.0.1:8080`.

### Примеры запросов

**Зарегистрироваться:**

```bash
curl -X POST http://127.0.0.1:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.ru", "password": "userpass123"}'
```

**Войти и получить JWT-токен:**

```bash
curl -X POST http://127.0.0.1:8000/auth/jwt/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=user@example.ru&password=userpass123"
```

**Создать игру (нужен токен суперюзера):**

```bash
curl -X POST http://127.0.0.1:8000/boardgames/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <YOUR_JWT_TOKEN>" \
  -d '{
        "name": "Каркассон",
        "description": "Классическая стратегия про средневековье",
        "max_players": 5,
        "min_players": 2,
        "min_age": 7,
        "playtime_minutes": 60
      }'
```

**Забронировать игру (нужен токен авторизованного пользователя):**

```bash
curl -X POST http://127.0.0.1:8000/bookings/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <YOUR_JWT_TOKEN>" \
  -d '{
        "from_booking": "2026-12-01T18:00:00",
        "to_booking": "2026-12-01T19:30:00",
        "youngest_player_age": 20,
        "players_count": 4,
        "boardgame_id": 1
      }'
```

**Получить список своих бронирований:**

```bash
curl http://127.0.0.1:8000/bookings/my_bookings \
  -H "Authorization: Bearer <YOUR_JWT_TOKEN>"
```

**Посмотреть будущие брони игры:**

```bash
curl http://127.0.0.1:8000/boardgames/1/bookings
```

### Примеры ответов API

**Создание игры (`201 Created`):**

```json
{
  "id": 1,
  "name": "Каркассон",
  "description": "Классическая стратегия про средневековье",
  "max_players": 5,
  "min_players": 2,
  "min_age": 7,
  "playtime_minutes": 60,
  "is_available": true
}
```

Игра без описания — поле `description` отсутствует в ответе:

```json
{
  "id": 2,
  "name": "Манчкин",
  "max_players": 6,
  "min_players": 3,
  "min_age": 12,
  "playtime_minutes": 45,
  "is_available": true
}
```

**Создание бронирования (`201 Created`):**

```json
{
  "id": 1,
  "from_booking": "2026-12-01T18:00:00",
  "to_booking": "2026-12-01T19:30:00",
  "youngest_player_age": 20,
  "players_count": 4,
  "boardgame_id": 1,
  "user_id": 2
}
```

**Свои бронирования (`200 OK`)** — `user_id` намеренно не возвращается:

```json
[
  {
    "id": 1,
    "from_booking": "2026-12-01T18:00:00",
    "to_booking": "2026-12-01T19:30:00",
    "youngest_player_age": 20,
    "players_count": 4,
    "boardgame_id": 1
  }
]
```

**Ошибка — дубликат названия игры (`422 Unprocessable Entity`):**

```json
{
  "detail": "Настольная игра с таким именем уже существует!"
}
```

**Ошибка — время уже занято (`422 Unprocessable Entity`):**

```json
{
  "detail": {
    "message": "Игра уже забронирована на это время",
    "conflicts": [
      {
        "from_booking": "2026-12-01T18:00:00",
        "to_booking": "2026-12-01T19:30:00"
      }
    ]
  }
}
```

**Ошибка — нарушение правил игры (`422 Unprocessable Entity`):**

```json
{
  "detail": "players_count вне диапазона игры (2-5)"
}
```

**Ошибка — игра не найдена (`404 Not Found`):**

```json
{
  "detail": "Настольная игра не найдена!"
}
```

**Ошибка — чужая бронь (`403 Forbidden`):**

```json
{
  "detail": "Невозможно удалить чужую бронь!"
}
```

## Проверка кода

Проект настроен на flake8 (максимальная длина строки — 79 символов). Зависимости
для проверки кода и тестов находятся в `requirements-dev.txt`:

```bash
pip install -r requirements-dev.txt
flake8
```

Форматирование и сортировка импортов описаны в `pyproject.toml` (black, isort).

## Структура проекта

```
boardgame-booking-api/
├── app/                        # Основное приложение
│   ├── main.py                 # Точка входа FastAPI + lifespan
│   ├── api/                    # API-слой
│   │   ├── routers.py          # Агрегатор маршрутов
│   │   ├── validators.py       # Валидаторы (дубликаты, правила брони, пересечения)
│   │   └── endpoints/          # Роутеры по сущностям
│   │       ├── boardgame.py
│   │       ├── booking.py
│   │       └── user.py         # Аутентификация и пользователи
│   ├── core/                   # Инфраструктура
│   │   ├── base.py             # Импорты Base и моделей для Alembic
│   │   ├── config.py           # Настройки (pydantic-settings)
│   │   ├── constants.py        # Константы (лимиты, длины, JWT_LIFETIME)
│   │   ├── db.py               # Async-движок, Base, CommonMixin, сессии
│   │   ├── init_db.py          # Создание первого суперюзера
│   │   └── user.py             # Менеджер пользователей, JWT-бэкенд, зависимости
│   ├── crud/                   # Слой доступа к данным
│   │   ├── base.py             # Базовый CRUD
│   │   ├── boardgame.py
│   │   └── booking.py
│   ├── models/                 # SQLAlchemy-модели
│   │   ├── boardgame.py
│   │   ├── booking.py
│   │   └── user.py
│   └── schemas/                # Pydantic-схемы
│       ├── boardgame.py
│       ├── booking.py
│       └── user.py
├── alembic/                    # Миграции Alembic
│   └── versions/
├── Dockerfile                  # Сборка образа backend (python:3.12-slim + uvicorn)
├── docker-compose.yml          # Сервисы db (PostgreSQL 16) и backend
├── .dockerignore               # Исключения для сборки образа (.env, venv, tests)
├── .env.example                # Шаблон переменных окружения (SQLite / PostgreSQL)
├── alembic.ini
├── pyproject.toml
├── requirements.txt            # Прикладные зависимости
├── requirements-dev.txt        # Зависимости для разработки и линтера
├── setup.cfg                   # Конфигурация flake8
├── .flake8
└── README.md
```

## Использованные технологии

| Технология | Назначение |
| ---------- | ---------- |
| [Python](https://www.python.org/) | Язык программирования |
| [FastAPI](https://fastapi.tiangolo.com/) | Асинхронный веб-фреймворк |
| [SQLAlchemy 2.0](https://docs.sqlalchemy.org/) | Async ORM для работы с БД |
| [Alembic](https://alembic.sqlalchemy.org/) | Миграции базы данных |
| [Pydantic v2](https://docs.pydantic.dev/) | Валидация и сериализация данных |
| [pydantic-settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/) | Настройки из переменных окружения |
| [asyncpg](https://github.com/MagicStack/asyncpg) | Async-драйвер PostgreSQL |
| [aiosqlite](https://github.com/omnilib/aiosqlite) | Async-драйвер SQLite (локальная разработка) |
| [fastapi-users](https://github.com/fastapi-users/fastapi-users) | Аутентификация и JWT-токены |
| [fastapi-users-db-sqlalchemy](https://github.com/fastapi-users/fastapi-users-db-sqlalchemy) | Хранилище пользователей для fastapi-users |
| [Docker](https://www.docker.com/) | Контейнеризация |
| [Docker Compose](https://docs.docker.com/compose/) | Оркестрация контейнеров |
| [Uvicorn](https://www.uvicorn.org/) | ASGI-сервер |
| [flake8](https://flake8.pycqa.org/) | Проверка стиля кода |

## Автор

| Имя | GitHub |
| --- | ------ |
| Юлия Тарханова | [@TAKOYAMItakoyami](https://github.com/TAKOYAMItakoyami) |

## Лицензия

Проект распространяется под лицензией MIT.
