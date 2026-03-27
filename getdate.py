"""
getdate.py - Parse natural language date expressions into datetime objects.

Returns timezone-aware datetime.datetime objects.
Supports relative expressions, ordinal days, and various date formats.
"""

import re
from datetime import datetime, timedelta, date
from typing import Optional


class DateParseError(Exception):
    """Raised when a date expression cannot be parsed."""

    pass


DAYS = {
    "monday": 0,
    "tuesday": 1,
    "wednesday": 2,
    "thursday": 3,
    "friday": 4,
    "saturday": 5,
    "sunday": 6,
    "mon": 0,
    "tue": 1,
    "wed": 2,
    "thu": 3,
    "fri": 4,
    "sat": 5,
    "sun": 6,
}

MONTHS = {
    "january": 1,
    "february": 2,
    "march": 3,
    "april": 4,
    "may": 5,
    "june": 6,
    "july": 7,
    "august": 8,
    "september": 9,
    "october": 10,
    "november": 11,
    "december": 12,
    "jan": 1,
    "feb": 2,
    "mar": 3,
    "apr": 4,
    "jun": 6,
    "jul": 7,
    "aug": 8,
    "sep": 9,
    "oct": 10,
    "nov": 11,
    "dec": 12,
}

ORDINALS = {
    "first": 1,
    "second": 2,
    "third": 3,
    "fourth": 4,
    "fifth": 5,
    "sixth": 6,
    "seventh": 7,
    "eighth": 8,
    "ninth": 9,
    "tenth": 10,
    "eleventh": 11,
    "twelfth": 12,
    "1st": 1,
    "2nd": 2,
    "3rd": 3,
    "4th": 4,
    "5th": 5,
    "6th": 6,
    "7th": 7,
    "8th": 8,
    "9th": 9,
    "10th": 10,
    "11th": 11,
    "12th": 12,
}

LOCAL_TZ = datetime.now().astimezone().tzinfo


def _get_now() -> datetime:
    return datetime.now(tz=LOCAL_TZ)


def getdate(buf: str) -> Optional[datetime]:
    """
    Parse a date expression and return a timezone-aware datetime.

    Args:
        buf: Date expression string

    Returns:
        timezone-aware datetime object, or None if parsing fails
    """
    if not buf or not isinstance(buf, str):
        return None

    buf = buf.strip()
    if not buf:
        return None

    buf_lower = buf.lower()

    from parser import getdate_with_lexer

    result = getdate_with_lexer(buf_lower)
    if result is not None:
        return result

    now = _get_now()

    parsers = [
        _parse_absolute_numeric,
        _parse_iso8601,
        _parse_us_datetime,
        _parse_relative_offset,
        _parse_relative_with_time,
        _parse_relative_day,
        _parse_ordinal_day,
        _parse_relative_unit,
    ]

    for parser in parsers:
        try:
            result = parser(buf_lower, now)
            if result is not None:
                return result
        except DateParseError:
            continue

    return None


def _parse_absolute_numeric(buf: str, now: datetime) -> Optional[datetime]:
    """Parse YYYYMMDDHHMM format like 202603062145"""
    pattern = r"^(\d{4})(\d{2})(\d{2})(\d{2})(\d{2})$"
    match = re.match(pattern, buf)
    if match:
        year, month, day, hour, minute = map(int, match.groups())
        try:
            return datetime(year, month, day, hour, minute, tzinfo=LOCAL_TZ)
        except ValueError:
            raise DateParseError("Invalid date values")
    return None


def _parse_iso8601(buf: str, now: datetime) -> Optional[datetime]:
    """Parse ISO 8601 formats."""
    from datetime import timezone

    pattern = r"^(\d{4})-(\d{2})-(\d{2})[T ](\d{2}):(\d{2}):(\d{2})(?:\.(\d+))?(Z|[+-]\d{2}:?\d{2})?$"
    match = re.match(pattern, buf, re.IGNORECASE)
    if match:
        groups = match.groups()
        year, month, day, hour, minute, second = map(int, groups[:6])
        tz = groups[7]
        if tz and tz.upper() == "Z":
            tzinfo = timezone.utc
        elif tz:
            sign = 1 if tz[0] == "+" else -1
            tz_h = int(tz[1:3])
            tz_str = tz[3:]
            if tz_str.startswith(":"):
                tz_str = tz_str[1:]
            tz_m = int(tz_str) if tz_str else 0
            tzinfo = timezone(timedelta(hours=sign * tz_h, minutes=sign * tz_m))
        else:
            tzinfo = LOCAL_TZ
        try:
            return datetime(year, month, day, hour, minute, second, tzinfo=tzinfo)
        except ValueError:
            raise DateParseError("Invalid ISO date")

    pattern = r"^(\d{4})-(\d{2})-(\d{2})$"
    match = re.match(pattern, buf)
    if match:
        year, month, day = map(int, match.groups())
        try:
            return datetime(year, month, day, tzinfo=LOCAL_TZ)
        except ValueError:
            raise DateParseError("Invalid date")

    return None


def _parse_us_datetime(buf: str, now: datetime) -> Optional[datetime]:
    """Parse US date formats like 3/5/2026 21:45 or 3/5/2026 9:45p"""

    pattern = r"^(\d{1,2})/(\d{1,2})/(\d{2,4})(?:\s+(\d{1,2}):(\d{2})(?::(\d{2}))?\s*(a|p|am|pm)?)?$"
    match = re.match(pattern, buf, re.IGNORECASE)
    if match:
        groups = match.groups()
        month, day = int(groups[0]), int(groups[1])

        year_str = groups[2]
        if len(year_str) == 2:
            year = 2000 + int(year_str)
            if year < 1970:
                year += 100
        else:
            year = int(year_str)

        if groups[3]:
            hour = int(groups[3])
            minute = int(groups[4])
            second = int(groups[5]) if groups[5] else 0
            ampm = groups[6]
            if ampm:
                ampm = ampm.lower()
                if ampm == "p" or ampm == "pm":
                    if hour != 12:
                        hour += 12
                elif ampm == "a" or ampm == "am":
                    if hour == 12:
                        hour = 0
        else:
            hour, minute, second = 0, 0, 0

        try:
            return datetime(year, month, day, hour, minute, second, tzinfo=LOCAL_TZ)
        except ValueError:
            raise DateParseError("Invalid US date")

    return None


def _parse_time(time_str: str) -> Optional[tuple[int, int]]:
    """
    Parse a time string and return (hour, minute).
    Returns None if parsing fails.
    """
    time_str = time_str.lower().strip()

    special_times = {
        "noon": (12, 0),
        "midday": (12, 0),
        "midnight": (0, 0),
        "night": (21, 0),
    }
    if time_str in special_times:
        return special_times[time_str]

    pattern = r"^(\d{1,2}):(\d{2})(?::(\d{2}))?\s*(a|p|am|pm)?$"
    match = re.match(pattern, time_str, re.IGNORECASE)
    if match:
        hour = int(match.group(1))
        minute = int(match.group(2))
        ampm = match.group(4)

        if ampm:
            ampm = ampm.lower()
            if ampm == "p" or ampm == "pm":
                if hour != 12:
                    hour += 12
            elif ampm == "a" or ampm == "am":
                if hour == 12:
                    hour = 0

        if 0 <= hour <= 23 and 0 <= minute <= 59:
            return (hour, minute)

    pattern = r"^(\d{1,2})\s*(a|p|am|pm)?$"
    match = re.match(pattern, time_str, re.IGNORECASE)
    if match:
        hour = int(match.group(1))
        ampm = match.group(2)

        if ampm:
            ampm = ampm.lower()
            if ampm == "p" or ampm == "pm":
                if hour != 12:
                    hour += 12
            elif ampm == "a" or ampm == "am":
                if hour == 12:
                    hour = 0

        if 0 <= hour <= 23:
            return (hour, 0)

    return None


def _parse_relative_with_time(buf: str, now: datetime) -> Optional[datetime]:
    """Parse relative day expressions with time like 'tomorrow 2pm', 'friday 2pm'."""

    simple_relative = {
        "today": 0,
        "yesterday": -1,
        "tomorrow": 1,
    }

    for rel_day, day_offset in simple_relative.items():
        prefix = rel_day + " "
        if buf.startswith(prefix):
            time_str = buf[len(prefix) :].strip()
            time_parsed = _parse_time(time_str)
            if time_parsed:
                hour, minute = time_parsed
                target_date = now + timedelta(days=day_offset)
                return datetime(
                    target_date.year,
                    target_date.month,
                    target_date.day,
                    hour,
                    minute,
                    0,
                    tzinfo=LOCAL_TZ,
                )

    pattern = r"^(next|last|previous)\s+(monday|tuesday|wednesday|thursday|friday|saturday|sunday|mon|tue|wed|thu|fri|sat|sun)\s+(\d{1,2}(?::\d{2})?(?:\s*[ap]\.?m\.?)?)$"
    match = re.match(pattern, buf, re.IGNORECASE)
    if match:
        direction, day_name, time_str = match.groups()
        target_day = DAYS[day_name]
        time_parsed = _parse_time(time_str)

        if time_parsed:
            hour, minute = time_parsed
        else:
            return None

        days_ahead = target_day - now.weekday()
        if direction.lower() == "next":
            if days_ahead <= 0:
                days_ahead += 7
        else:
            if days_ahead >= 0:
                days_ahead -= 7

        target_date = now + timedelta(days=days_ahead)
        return datetime(
            target_date.year,
            target_date.month,
            target_date.day,
            hour,
            minute,
            0,
            tzinfo=LOCAL_TZ,
        )

    time_match = re.search(r"(\d{1,2}(?::\d{2})?(?:\s*[ap]\.?m\.?)?)$", buf)
    if time_match:
        time_str = time_match.group(1)
        day_part = buf[: time_match.start()].strip()

        if day_part in DAYS:
            target_day = DAYS[day_part]
            time_parsed = _parse_time(time_str)

            if time_parsed:
                hour, minute = time_parsed
                days_ahead = target_day - now.weekday()
                if days_ahead <= 0:
                    days_ahead += 7

                target_date = now + timedelta(days=days_ahead)
                return datetime(
                    target_date.year,
                    target_date.month,
                    target_date.day,
                    hour,
                    minute,
                    0,
                    tzinfo=LOCAL_TZ,
                )

    return None


def _parse_relative_offset(buf: str, now: datetime) -> Optional[datetime]:
    """Parse offset expressions like +2 days, 3 days ago, 72 hours from now."""

    pattern = r"^([+-]?)(\d+)\s+(days?|weeks?|months?|hours?|minutes?|seconds?)\s*(ago|from now)?$"
    match = re.match(pattern, buf)
    if match:
        sign_str, amount, unit, direction = match.groups()
        amount = int(amount)

        sign = -1 if (sign_str == "-" or direction == "ago") else 1
        amount *= sign

        if unit.startswith("day"):
            return now + timedelta(days=amount)
        elif unit.startswith("week"):
            return now + timedelta(weeks=amount)
        elif unit.startswith("month"):
            month = now.month + amount
            year = now.year
            while month > 12:
                month -= 12
                year += 1
            while month < 1:
                month += 12
                year -= 1
            try:
                return datetime(
                    year,
                    month,
                    now.day,
                    now.hour,
                    now.minute,
                    now.second,
                    tzinfo=LOCAL_TZ,
                )
            except ValueError:
                day = min(now.day, 28)
                return datetime(
                    year, month, day, now.hour, now.minute, now.second, tzinfo=LOCAL_TZ
                )
        elif unit.startswith("hour"):
            return now + timedelta(hours=amount)
        elif unit.startswith("minute"):
            return now + timedelta(minutes=amount)
        elif unit.startswith("second"):
            return now + timedelta(seconds=amount)

    return None


def _parse_relative_day(buf: str, now: datetime) -> Optional[datetime]:
    """Parse relative day expressions like next thursday, last friday."""

    pattern = r"^(next|last|previous)\s+(monday|tuesday|wednesday|thursday|friday|saturday|sunday|mon|tue|wed|thu|fri|sat|sun)$"
    match = re.match(pattern, buf)
    if match:
        direction, day_name = match.groups()
        target_day = DAYS[day_name]

        days_ahead = target_day - now.weekday()
        if direction == "next":
            if days_ahead <= 0:
                days_ahead += 7
        else:
            if days_ahead >= 0:
                days_ahead -= 7

        return now + timedelta(days=days_ahead)

    if buf in DAYS:
        target_day = DAYS[buf]
        days_ahead = target_day - now.weekday()
        if days_ahead <= 0:
            days_ahead += 7
        return now + timedelta(days=days_ahead)

    return None


def _parse_ordinal_day(buf: str, now: datetime) -> Optional[datetime]:
    """Parse ordinal day expressions like 2nd wednesday of march 2026."""

    pattern = r"^(\d+(?:st|nd|rd|th)?|first|second|third|fourth|fifth)\s+(monday|tuesday|wednesday|thursday|friday|saturday|sunday|mon|tue|wed|thu|fri|sat|sun)\s+(?:of\s+)?(?:(january|february|march|april|may|june|july|august|september|october|november|december|jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\s+)?(\d{4})?"
    match = re.match(pattern, buf)
    if match:
        ordinal_str, day_name, month_str, year_str = match.groups()

        ordinal_match = re.match(r"\d+", ordinal_str)
        ordinal = ORDINALS.get(
            ordinal_str, int(ordinal_match.group()) if ordinal_match else 1
        )
        target_day = DAYS[day_name]

        if month_str:
            month = MONTHS[month_str]
        else:
            month = now.month

        year = int(year_str) if year_str else now.year

        count = 0
        for d in range(1, 32):
            try:
                dt = date(year, month, d)
            except ValueError:
                break
            if dt.weekday() == target_day:
                count += 1
                if count == ordinal:
                    return datetime(
                        year,
                        month,
                        d,
                        now.hour,
                        now.minute,
                        now.second,
                        tzinfo=LOCAL_TZ,
                    )

        raise DateParseError(f"No {ordinal_str} {day_name} in {month}/{year}")

    pattern = r"^final\s+(monday|tuesday|wednesday|thursday|friday|saturday|sunday|mon|tue|wed|thu|fri|sat|sun)\s+(?:of\s+)?(?:(january|february|march|april|may|june|july|august|september|october|november|december|jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\s+)?(\d{4})?"
    match = re.match(pattern, buf)
    if match:
        day_name, month_str, year_str = match.groups()
        target_day = DAYS[day_name]

        if month_str:
            month = MONTHS[month_str]
        else:
            month = now.month

        year = int(year_str) if year_str else now.year

        last_occurrence = None
        for d in range(31, 0, -1):
            try:
                dt = date(year, month, d)
            except ValueError:
                continue
            if dt.weekday() == target_day:
                last_occurrence = d
                break

        if last_occurrence:
            return datetime(
                year,
                month,
                last_occurrence,
                now.hour,
                now.minute,
                now.second,
                tzinfo=LOCAL_TZ,
            )

        raise DateParseError(f"No {day_name} in {month}/{year}")

    return None


def _parse_relative_unit(buf: str, now: datetime) -> Optional[datetime]:
    """Parse relative unit expressions like next week, next month, yesterday, tomorrow."""

    simple_mapping = {
        "today": 0,
        "yesterday": -1,
        "tomorrow": 1,
        "now": 0,
    }

    if buf in simple_mapping:
        return now + timedelta(days=simple_mapping[buf])

    pattern = r"^(next|last|previous)\s+(week|month|year)$"
    match = re.match(pattern, buf)
    if match:
        direction, unit = match.groups()

        if unit == "week":
            days = 7 if direction == "next" else -7
            return now + timedelta(days=days)
        elif unit == "month":
            month = now.month + (1 if direction == "next" else -1)
            year = now.year
            while month > 12:
                month -= 12
                year += 1
            while month < 1:
                month += 12
                year -= 1
            try:
                return datetime(
                    year,
                    month,
                    now.day,
                    now.hour,
                    now.minute,
                    now.second,
                    tzinfo=LOCAL_TZ,
                )
            except ValueError:
                day = min(now.day, 28)
                return datetime(
                    year, month, day, now.hour, now.minute, now.second, tzinfo=LOCAL_TZ
                )
        elif unit == "year":
            year = now.year + (1 if direction == "next" else -1)
            try:
                return datetime(
                    year,
                    now.month,
                    now.day,
                    now.hour,
                    now.minute,
                    now.second,
                    tzinfo=LOCAL_TZ,
                )
            except ValueError:
                day = min(now.day, 28)
                return datetime(
                    year,
                    now.month,
                    day,
                    now.hour,
                    now.minute,
                    now.second,
                    tzinfo=LOCAL_TZ,
                )

    return None


def verify_valid_date_expression(buf: str) -> bool:
    """Verify if a string is a valid date expression."""
    return getdate(buf) is not None


if __name__ == "__main__":
    import sys

    test_cases = [
        "now",
        "today",
        "yesterday",
        "tomorrow",
        "+2 days",
        "-3 days",
        "3 days ago",
        "next week",
        "last week",
        "next month",
        "next year",
        "next thursday",
        "last friday",
        "2nd wednesday of march 2026",
        "1st monday of march",
        "final friday of march 2026",
        "2026-03-06",
        "2026-03-06T14:30:00Z",
        "202603062145",
    ]

    if len(sys.argv) > 1:
        test_cases = sys.argv[1:]

    for tc in test_cases:
        result = getdate(tc)
        if result:
            print(f"{tc!r:40} -> {result}")
        else:
            print(f"{tc!r:40} -> FAILED")
