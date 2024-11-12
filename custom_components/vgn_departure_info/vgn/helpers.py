from datetime import date, datetime, timedelta

import logging
import re

_LOGGER = logging.getLogger(__name__)


def datestr_to_date(
    x: date | str, format_str: str = "%Y%m%d", *, inverse: bool = False
) -> str | date:
    if x is None:
        return None
    if not inverse:
        result = datetime.strptime(x, format_str).date()
    else:
        result = x.strftime(format_str)
    return result


def weekday_to_str(weekday: int | str, *, inverse: bool = False) -> int | str:
    s = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
    if not inverse:
        try:
            return s[weekday]
        except Exception:
            return
    else:
        try:
            return s.index(weekday)
        except Exception:
            return


def gtfs_time_to_datetime(date: str, time: str):
    if not date or not isinstance(date, str):
        raise ValueError("")

    if not time or not isinstance(time, str):
        raise ValueError("")

    if not re.fullmatch(r"\d{8}", date):
        raise ValueError("")

    if not re.fullmatch(r"\d{2}:\d{2}:\d{2}", time):
        raise ValueError("")

    (hour, minute, sec) = (int(x) for x in time.split(":"))

    overnight = False

    if hour > 30:
        raise ValueError("")
    if hour >= 24:
        hour %= 24
        overnight = True

    result = datetime.strptime(f"{date} {hour}:{minute}:{sec}", "%Y%m%d %H:%M:%S")

    if overnight:
        result += timedelta(days=1)

    return result
