from datetime import timedelta

from app.core.constants import SECONDS_IN_HOUR, SECONDS_IN_MINUTE


def format_time_delta(time_pass: timedelta) -> str:
    """
    Утилита для форматирования времени.
    """
    days = time_pass.days
    hours = time_pass.seconds // SECONDS_IN_HOUR
    minutes = (time_pass.seconds % SECONDS_IN_HOUR) // SECONDS_IN_MINUTE
    if days > 0:
        return f"{days} дн. {hours} ч."
    if hours > 0:
        return f"{hours} ч. {minutes} мин."
    return f"{minutes} мин."
