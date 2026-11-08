import io
from collections import namedtuple
from datetime import datetime
from typing import Any, Final

import xlsxwriter  # type: ignore
from xlsxwriter.utility import xl_rowcol_to_cell  # type: ignore

from app.core.config import settings
from app.core.constants import (
    REPORT_TOP_LIMIT,
    REPORTS_FOLDER_DEFAULT,
    SECONDS_IN_MINUTE,
    ReportKey,
)
from app.core.utils import format_time_delta
from app.core.yandex_client import YandexDiskClient

ReportColumn = namedtuple("ReportColumn", ("key", "header", "width"))

TEXT_GAME_NAME = "Название игры"
TEXT_BOOKINGS_COUNT = "Количество бронирований"
TEXT_BOOKINGS_COUNT_WEEK = "Количество бронирований за неделю"
TEXT_BOOKING_TIME_WEEK = "Общее время бронирования за неделю"
TEXT_PLAYERS_MIN = "Мин. количество игравших"
TEXT_PLAYERS_MAX = "Макс. количество игравших"
TEXT_TIME_MINUTES = "Время (минуты)"
TEXT_SHARE_OF_TIME = "Доля времени"

HEADER_NAME_WIDTH = 30
HEADER_BOOKINGS_COUNT_WIDTH = 35
HEADER_BOOKING_TIME_WIDTH = 35
HEADER_PLAYERS_COUNT_MIN_WIDTH = 25
HEADER_PLAYERS_COUNT_MAX_WIDTH = 25

REPORT_COLUMNS = (
    ReportColumn(
        key=ReportKey.NAME,
        header=TEXT_GAME_NAME,
        width=HEADER_NAME_WIDTH,
    ),
    ReportColumn(
        key=ReportKey.BOOKINGS_COUNT,
        header=TEXT_BOOKINGS_COUNT_WEEK,
        width=HEADER_BOOKINGS_COUNT_WIDTH,
    ),
    ReportColumn(
        key=ReportKey.BOOKING_TIME,
        header=TEXT_BOOKING_TIME_WEEK,
        width=HEADER_BOOKING_TIME_WIDTH,
    ),
    ReportColumn(
        key=ReportKey.PLAYERS_COUNT_MIN,
        header=TEXT_PLAYERS_MIN,
        width=HEADER_PLAYERS_COUNT_MIN_WIDTH,
    ),
    ReportColumn(
        key=ReportKey.PLAYERS_COUNT_MAX,
        header=TEXT_PLAYERS_MAX,
        width=HEADER_PLAYERS_COUNT_MAX_WIDTH,
    ),
)

REPORT_FILE_PREFIX = "Отчет"
REPORT_TITLE_PREFIX = "Отчет от"
REPORT_TOTAL_PREFIX = "Всего разных игр сыграно за неделю:"
FILENAME_CHAR_REPLACEMENTS: Final[dict[str, str | int | None]] = {
    ":": "-",
    ".": "-",
    " ": "_",
}

FIRST_COL_IDX = 0
TITLE_ROW_IDX = 0
HEADER_ROW_IDX = 1
DATA_START_ROW_IDX = HEADER_ROW_IDX + 1
TOTAL_ROW_GAP = 0

TITLE_FONT_SIZE = 16
TOTAL_FONT_SIZE = 14
BORDER_THIN = 1

FONT_COLOR_BLACK = "black"
ALIGN_LEFT = "left"
HEADER_BG_COLOR = "#3AB52F"

CELL_FORMAT = {"border": BORDER_THIN, "align": ALIGN_LEFT}
TITLE_FORMAT = {"bold": True, "font_size": TITLE_FONT_SIZE}
TOTAL_FORMAT = {
    **CELL_FORMAT,
    "bold": True,
    "font_size": TOTAL_FONT_SIZE,
}
HEADER_FORMAT = {
    **CELL_FORMAT,
    "bold": True,
    "bg_color": HEADER_BG_COLOR,
    "font_color": FONT_COLOR_BLACK,
}

MINUTES_NUM_FORMAT = '0 "мин."'
MINUTES_FORMAT = {**CELL_FORMAT, "num_format": MINUTES_NUM_FORMAT}

SHEET_FULL_REPORT = "Полный отчет"
SHEET_TOP_BOOKINGS = "Топ по броням"
SHEET_TOP_TIME = "Топ по времени"

TOP_HEADER_ROW_IDX = 0
TOP_DATA_START_ROW_IDX = TOP_HEADER_ROW_IDX + 1
TOP_NAME_COL_IDX = 0
TOP_VALUE_COL_IDX = TOP_NAME_COL_IDX + 1
TOP_SHEET_NAME_COL_WIDTH = 25
TOP_SHEET_VALUE_COL_WIDTH = 30

CHART_TYPE_BAR = "bar"
CHART_TYPE_PIE = "pie"
# Якорь чарта: на две колонки правее значений топ-листа.
CHART_ANCHOR_CELL = "D2"
CHART_HEIGHT = 450
BAR_CHART_SIZE = {"width": 800, "height": CHART_HEIGHT}
PIE_CHART_SIZE = {"width": 600, "height": CHART_HEIGHT}
CHART_AXIS_FONT_SIZE = 14
CHART_LABEL_FONT_SIZE = 14
CHART_TITLE_TOP_BOOKINGS = f"Топ-{REPORT_TOP_LIMIT} популярных игр"
CHART_TITLE_TOP_TIME = "Самые увлекательные игры (по времени)"


def _chart_series_range(
    sheet_name: str, col_idx: int, first_row_idx: int, last_row_idx: int
) -> str:
    """
    A1-диапазон столбца листа для ряда данных диаграммы.
    """
    first_cell = xl_rowcol_to_cell(first_row_idx, col_idx, True, True)
    last_cell = xl_rowcol_to_cell(last_row_idx, col_idx, True, True)
    return f"'{sheet_name}'!{first_cell}:{last_cell}"


async def set_user_permissions(
    file_path: str, yandex_client: YandexDiskClient
) -> str:
    """
    Делает файл публичным и возвращает ссылку.
    """
    return await yandex_client.publish_file(file_path)


async def create_simple_report(
    bookings: list[dict[str, Any]],
    yandex_client: YandexDiskClient,
    folder: str = REPORTS_FOLDER_DEFAULT,
) -> str:
    """
    Создаёт Excel-файл с тремя листами и загружает на Яндекс Диск.
    """
    now_date_time = datetime.now().strftime(settings.report_format)
    raw_filename = f"{REPORT_FILE_PREFIX}_{now_date_time}"
    safe_filename = raw_filename.translate(
        str.maketrans(FILENAME_CHAR_REPLACEMENTS)
    )

    upload_url, file_path = await yandex_client.create_excel_file(
        safe_filename, folder
    )

    output = io.BytesIO()
    workbook = xlsxwriter.Workbook(output)

    title_format = workbook.add_format(TITLE_FORMAT)
    total_format = workbook.add_format(TOTAL_FORMAT)
    header_format = workbook.add_format(HEADER_FORMAT)
    cell_format = workbook.add_format(CELL_FORMAT)
    minutes_format = workbook.add_format(MINUTES_FORMAT)

    last_col_idx = len(REPORT_COLUMNS) - 1

    # ==========================================
    # ЛИСТ 1: ПОЛНЫЙ ОТЧЕТ (СОРТИРОВКА ПО АЛФАВИТУ)
    # ==========================================
    ws_full = workbook.add_worksheet(SHEET_FULL_REPORT)

    ws_full.merge_range(
        TITLE_ROW_IDX,
        FIRST_COL_IDX,
        TITLE_ROW_IDX,
        last_col_idx,
        f"{REPORT_TITLE_PREFIX} {now_date_time}",
        title_format,
    )

    for num_col, column in enumerate(REPORT_COLUMNS):
        ws_full.write(HEADER_ROW_IDX, num_col, column.header, header_format)

    bookings_alpha = sorted(bookings, key=lambda x: x[ReportKey.NAME])

    for num_row, booking in enumerate(
        bookings_alpha, start=DATA_START_ROW_IDX
    ):
        for num_col, column in enumerate(REPORT_COLUMNS):
            cell_value = booking[column.key]
            if column.key == ReportKey.BOOKING_TIME:
                cell_value = format_time_delta(cell_value)
            ws_full.write(num_row, num_col, cell_value, cell_format)

    total_row_idx = DATA_START_ROW_IDX + len(bookings_alpha) + TOTAL_ROW_GAP

    ws_full.merge_range(
        total_row_idx,
        FIRST_COL_IDX,
        total_row_idx,
        last_col_idx,
        f"{REPORT_TOTAL_PREFIX} {len(bookings_alpha)}",
        total_format,
    )

    for num_col, column in enumerate(REPORT_COLUMNS):
        ws_full.set_column(num_col, num_col, column.width)

    # ==========================================
    # ЛИСТ 2: ТОП-10 ПО БРОНЯМ (СТОЛБЧАТАЯ ДИАГРАММА)
    # ==========================================
    ws_bookings = workbook.add_worksheet(SHEET_TOP_BOOKINGS)

    top_by_bookings = sorted(
        bookings, key=lambda x: x[ReportKey.BOOKINGS_COUNT], reverse=True
    )[:REPORT_TOP_LIMIT]

    ws_bookings.write(
        TOP_HEADER_ROW_IDX, TOP_NAME_COL_IDX, TEXT_GAME_NAME, header_format
    )
    ws_bookings.write(
        TOP_HEADER_ROW_IDX,
        TOP_VALUE_COL_IDX,
        TEXT_BOOKINGS_COUNT,
        header_format,
    )
    ws_bookings.set_column(
        TOP_NAME_COL_IDX, TOP_NAME_COL_IDX, TOP_SHEET_NAME_COL_WIDTH
    )
    ws_bookings.set_column(
        TOP_VALUE_COL_IDX, TOP_VALUE_COL_IDX, TOP_SHEET_VALUE_COL_WIDTH
    )

    for row_idx, game in enumerate(
        top_by_bookings, start=TOP_DATA_START_ROW_IDX
    ):
        ws_bookings.write(
            row_idx, TOP_NAME_COL_IDX, game[ReportKey.NAME], cell_format
        )
        ws_bookings.write(
            row_idx,
            TOP_VALUE_COL_IDX,
            game[ReportKey.BOOKINGS_COUNT],
            cell_format,
        )

    top_bookings_end_row = TOP_DATA_START_ROW_IDX + len(top_by_bookings) - 1
    chart = workbook.add_chart({"type": CHART_TYPE_BAR})
    chart.add_series(
        {
            "name": TEXT_BOOKINGS_COUNT,
            "categories": _chart_series_range(
                SHEET_TOP_BOOKINGS,
                TOP_NAME_COL_IDX,
                TOP_DATA_START_ROW_IDX,
                top_bookings_end_row,
            ),
            "values": _chart_series_range(
                SHEET_TOP_BOOKINGS,
                TOP_VALUE_COL_IDX,
                TOP_DATA_START_ROW_IDX,
                top_bookings_end_row,
            ),
            "fill": {"color": HEADER_BG_COLOR},
            "data_labels": {
                "value": True,
                "font": {
                    "size": CHART_LABEL_FONT_SIZE,
                    "bold": True,
                    "color": FONT_COLOR_BLACK,
                },
            },
        }
    )

    chart.set_title(
        {
            "name": CHART_TITLE_TOP_BOOKINGS,
            "name_font": {
                "size": TITLE_FONT_SIZE,
                "bold": True,
                "color": FONT_COLOR_BLACK,
            },
        }
    )
    chart.set_x_axis(
        {
            "name": TEXT_BOOKINGS_COUNT,
            "name_font": {
                "size": CHART_AXIS_FONT_SIZE,
                "color": FONT_COLOR_BLACK,
            },
            "num_font": {
                "size": CHART_AXIS_FONT_SIZE,
                "color": FONT_COLOR_BLACK,
            },
        }
    )
    chart.set_y_axis(
        {
            "name": TEXT_GAME_NAME,
            "reverse": True,
            "name_font": {
                "size": CHART_AXIS_FONT_SIZE,
                "color": FONT_COLOR_BLACK,
            },
            "num_font": {
                "size": CHART_AXIS_FONT_SIZE,
                "color": FONT_COLOR_BLACK,
            },
            "line": {"color": FONT_COLOR_BLACK},
        }
    )
    chart.set_legend({"none": True})
    chart.set_size(BAR_CHART_SIZE)
    ws_bookings.insert_chart(CHART_ANCHOR_CELL, chart)

    # ==========================================
    # ЛИСТ 3: ТОП-10 ПО ВРЕМЕНИ (КРУГОВАЯ ДИАГРАММА)
    # ==========================================
    ws_time = workbook.add_worksheet(SHEET_TOP_TIME)

    # Сортируем по времени
    top_by_time = sorted(
        bookings, key=lambda x: x[ReportKey.BOOKING_TIME], reverse=True
    )[:REPORT_TOP_LIMIT]

    ws_time.write(
        TOP_HEADER_ROW_IDX, TOP_NAME_COL_IDX, TEXT_GAME_NAME, header_format
    )
    ws_time.write(
        TOP_HEADER_ROW_IDX,
        TOP_VALUE_COL_IDX,
        TEXT_TIME_MINUTES,
        header_format,
    )
    ws_time.set_column(
        TOP_NAME_COL_IDX, TOP_NAME_COL_IDX, TOP_SHEET_NAME_COL_WIDTH
    )
    ws_time.set_column(
        TOP_VALUE_COL_IDX, TOP_VALUE_COL_IDX, TOP_SHEET_VALUE_COL_WIDTH
    )

    for row_idx, game in enumerate(top_by_time, start=TOP_DATA_START_ROW_IDX):
        minutes = int(
            game[ReportKey.BOOKING_TIME].total_seconds() // SECONDS_IN_MINUTE
        )
        ws_time.write(
            row_idx, TOP_NAME_COL_IDX, game[ReportKey.NAME], cell_format
        )
        ws_time.write(row_idx, TOP_VALUE_COL_IDX, minutes, minutes_format)

    pie_chart = workbook.add_chart({"type": CHART_TYPE_PIE})
    top_time_end_row = TOP_DATA_START_ROW_IDX + len(top_by_time) - 1
    pie_chart.add_series(
        {
            "name": TEXT_SHARE_OF_TIME,
            "categories": _chart_series_range(
                SHEET_TOP_TIME,
                TOP_NAME_COL_IDX,
                TOP_DATA_START_ROW_IDX,
                top_time_end_row,
            ),
            "values": _chart_series_range(
                SHEET_TOP_TIME,
                TOP_VALUE_COL_IDX,
                TOP_DATA_START_ROW_IDX,
                top_time_end_row,
            ),
            "data_labels": {
                "percentage": True,
                "font": {
                    "size": CHART_LABEL_FONT_SIZE,
                    "bold": True,
                    "color": FONT_COLOR_BLACK,
                },
            },
        }
    )

    pie_chart.set_title(
        {
            "name": CHART_TITLE_TOP_TIME,
            "name_font": {
                "size": TITLE_FONT_SIZE,
                "bold": True,
                "color": FONT_COLOR_BLACK,
            },
        }
    )
    pie_chart.set_size(PIE_CHART_SIZE)
    ws_time.insert_chart(CHART_ANCHOR_CELL, pie_chart)

    workbook.close()
    output.seek(0)

    await yandex_client.upload_file(upload_url, output.getvalue())
    return file_path
