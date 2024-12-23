from datetime import datetime
from typing import Union


def create_date(
    month: Union[int, str, float],
    day: Union[int, str, float],
    year: Union[int, str, float],
    format: str = "yyyy-mm-dd",
) -> str:
    """
    Create a date string from month, day, and year components.

    Args:
        month: Month as integer, string, or float
        day: Day as integer, string, or float
        year: Year as integer, string, or float
        format: Output format (yyyy-mm-dd, mm/dd/yyyy, or mm-dd-yyyy)

    Returns:
        Formatted date string
    """
    try:
        # Convert inputs to integers
        month = int(float(month))
        day = int(float(day))
        year = int(float(year))

        # Validate date components
        if month < 1 or month > 12 or day < 1 or day > 31 or year < 1900:
            raise ValueError(
                f"Invalid date components: month={month}, day={day}, year={year}"
            )

        # Create base date string with zero padding
        if format.lower() == "yyyy-mm-dd":
            return f"{year:04d}-{month:02d}-{day:02d}"
        elif format.lower() == "mm/dd/yyyy":
            return f"{month:02d}/{day:02d}/{year:04d}"
        elif format.lower() == "mm-dd-yyyy":
            return f"{month:02d}-{day:02d}-{year:04d}"
        else:
            # Default to ISO format
            return f"{year:04d}-{month:02d}-{day:02d}"

    except Exception as e:
        raise ValueError(
            f"Error creating date: {str(e)}. Values - Month: {month}, Day: {day}, Year: {year}"
        )
