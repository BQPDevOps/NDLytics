from datetime import datetime
from typing import Union


def truncate_text(text: str, max_length: int = 50) -> str:
    return text[:max_length] + "..." if len(text) > max_length else text


def get_ordinal_suffix(day: int) -> str:
    if 10 <= day % 100 <= 20:
        suffix = "th"
    else:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(day % 10, "th")
    return suffix


def get_ordinal_suffix(day: int) -> str:
    if 10 <= day % 100 <= 20:
        suffix = "th"
    else:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(day % 10, "th")
    return suffix


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


__all__ = ["create_date", "get_ordinal_suffix", "truncate_text"]
