from datetime import datetime
from typing import Union


def _infer_format(format_str: str) -> str:
    # Convert human readable format to datetime format
    format_map = {
        "yyyy": "%Y",
        "yy": "%y",
        "mm": "%m",
        "m": "%-m",
        "dd": "%d",
        "d": "%-d",
    }

    # Handle example date format
    if any(c.isdigit() for c in format_str):
        if "-" in format_str:
            return "%Y-%m-%d"
        elif "/" in format_str:
            return "%m/%d/%Y"
        return "%Y%m%d"

    # Convert human format
    format_str = format_str.lower()
    for human_fmt, dt_fmt in format_map.items():
        format_str = format_str.replace(human_fmt, dt_fmt)
    return format_str


def create_date(
    month: Union[int, str, float],
    day: Union[int, str, float],
    year: Union[int, str, float],
    format: str = "yyyy-mm-dd",
) -> str:
    # Convert inputs to integers
    month = int(float(month))
    day = int(float(day))
    year = int(float(year))

    # Create date object
    date = datetime(year, month, day)

    # Convert format string and return
    dt_format = _infer_format(format)
    return date.strftime(dt_format)
