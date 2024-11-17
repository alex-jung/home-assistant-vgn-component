"""Helper classes."""

from datetime import date, datetime


def datestr_to_date(x: str, format_str: str = "%Y%m%d") -> date:
    """Convert date as string to date object."""
    if x is None:
        return None

    return datetime.strptime(x, format_str).date()


def weekday_to_str(weekday: int) -> str | None:
    """Return weekday as string."""
    s = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
    try:
        return s[weekday]
    except IndexError:
        return None
