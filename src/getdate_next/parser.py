"""
parser.py - Token stream to datetime conversion.

Parses tokenized date expressions into datetime objects.
"""

import re
from datetime import datetime, timedelta, date, timezone
from typing import Optional
from dataclasses import dataclass

from .lexer import Token, TokenType, tokenize


class DateParseError(Exception):
    """Raised when a date expression cannot be parsed."""

    pass


LOCAL_TZ = datetime.now().astimezone().tzinfo

DAYS_MAP = {
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

MONTHS_MAP = {
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

ORDINALS_MAP = {
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


@dataclass
class ParsedRelative:
    modifier: Optional[str] = None
    day: Optional[int] = None
    ordinal: Optional[int] = None
    month: Optional[int] = None
    year: Optional[int] = None
    offset_value: Optional[int] = None
    offset_unit: Optional[str] = None
    offset_direction: Optional[str] = None
    time_hour: Optional[int] = None
    time_minute: Optional[int] = None
    is_simple: bool = False
    simple_type: Optional[str] = None


class Parser:
    def __init__(self, tokens: list[Token]):
        self.tokens = tokens
        self.pos = 0
        self.now = datetime.now(tz=LOCAL_TZ)

    def peek(self) -> Token:
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return self.tokens[-1]

    def advance(self) -> Token:
        tok = self.peek()
        self.pos += 1
        return tok

    def expect(self, token_type: TokenType) -> Token:
        tok = self.peek()
        if tok.type != token_type:
            raise DateParseError(f"Expected {token_type}, got {tok.type}")
        return self.advance()

    def parse(self) -> Optional[datetime]:
        if not self.tokens or self.tokens[0].type == TokenType.EOF:
            return None

        parsers = [
            self._parse_absolute_numeric,
            self._parse_iso8601,
            self._parse_us_datetime,
            self._parse_relative_with_time,
            self._parse_relative_offset,
            self._parse_relative_day,
            self._parse_ordinal_day,
            self._parse_relative_unit,
        ]

        for parser in parsers:
            try:
                result = parser()
                if result is not None:
                    return result
            except DateParseError:
                continue

        return None

    def _parse_time(self, time_val: str) -> Optional[tuple[int, int]]:
        time_val = time_val.lower().strip()

        special_times = {
            "noon": (12, 0),
            "midday": (12, 0),
            "midnight": (0, 0),
            "night": (21, 0),
            "morning": (9, 0),
            "evening": (18, 0),
        }
        if time_val in special_times:
            return special_times[time_val]

        pattern = r"^(\d{1,2}):(\d{2})(?::(\d{2}))?\s*(a|p|am|pm)?$"
        match = re.match(pattern, time_val, re.IGNORECASE)
        if match:
            hour = int(match.group(1))
            minute = int(match.group(2))
            ampm = match.group(4)

            if ampm:
                ampm = ampm.lower()
                if ampm in ("p", "pm"):
                    if hour != 12:
                        hour += 12
                elif ampm in ("a", "am"):
                    if hour == 12:
                        hour = 0

            if 0 <= hour <= 23 and 0 <= minute <= 59:
                return (hour, minute)

        pattern = r"^(\d{1,2})\s*(a|p|am|pm)?$"
        match = re.match(pattern, time_val, re.IGNORECASE)
        if match:
            hour = int(match.group(1))
            ampm = match.group(2)

            if ampm:
                ampm = ampm.lower()
                if ampm in ("p", "pm"):
                    if hour != 12:
                        hour += 12
                elif ampm in ("a", "am"):
                    if hour == 12:
                        hour = 0

            if 0 <= hour <= 23:
                return (hour, 0)

        return None

    def _parse_absolute_numeric(self) -> Optional[datetime]:
        if self.pos != 0:
            return None

        buf = self.tokens[0].value if self.tokens else ""
        if len(buf) != 12 or not buf.isdigit():
            return None

        try:
            year = int(buf[0:4])
            month = int(buf[4:6])
            day = int(buf[6:8])
            hour = int(buf[8:10])
            minute = int(buf[10:12])
            return datetime(year, month, day, hour, minute, tzinfo=LOCAL_TZ)
        except ValueError:
            raise DateParseError("Invalid date")

    def _parse_iso8601(self) -> Optional[datetime]:
        buf = "".join(tok.value for tok in self.tokens if tok.type != TokenType.EOF)
        if "-" not in buf and "T" not in buf:
            return None

        pattern = r"^(\d{4})-(\d{2})-(\d{2})[T ](\d{2}):(\d{2}):(\d{2})(?:\.(\d+))?(Z|[+-]\d{2}:?\d{2})?$"
        m = re.match(pattern, buf, re.IGNORECASE)
        if m:
            groups = m.groups()
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
        m = re.match(pattern, buf)
        if m:
            year, month, day = map(int, m.groups())
            try:
                return datetime(year, month, day, tzinfo=LOCAL_TZ)
            except ValueError:
                raise DateParseError("Invalid date")

        return None

    def _parse_us_datetime(self) -> Optional[datetime]:
        has_sep = False
        for tok in self.tokens:
            if tok.type == TokenType.DATE_SEPARATOR:
                has_sep = True
                break

        if not has_sep:
            return None

        buf = "".join(tok.value for tok in self.tokens if tok.type != TokenType.EOF)
        pattern = r"^(\d{1,2})/(\d{1,2})/(\d{2,4})(?:\s+(\d{1,2}):(\d{2})(?::(\d{2}))?\s*(a|p|am|pm)?)?$"
        m = re.match(pattern, buf, re.IGNORECASE)
        if m:
            groups = m.groups()
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
                    if ampm in ("p", "pm"):
                        if hour != 12:
                            hour += 12
                    elif ampm in ("a", "am"):
                        if hour == 12:
                            hour = 0
            else:
                hour, minute, second = 0, 0, 0

            try:
                return datetime(year, month, day, hour, minute, second, tzinfo=LOCAL_TZ)
            except ValueError:
                raise DateParseError("Invalid US date")

        return None

    def _parse_relative_with_time(self) -> Optional[datetime]:
        saved_pos = self.pos

        simple_relative = {"today": 0, "yesterday": -1, "tomorrow": 1}

        tok1 = self.peek()
        if tok1.type == TokenType.WORD and tok1.value in simple_relative:
            self.advance()
            day_offset = simple_relative[tok1.value]

            if self.peek().type == TokenType.TIME:
                time_tok = self.advance()
                time_parsed = self._parse_time(time_tok.value)
                if time_parsed:
                    hour, minute = time_parsed
                    target_date = self.now + timedelta(days=day_offset)
                    return datetime(
                        target_date.year,
                        target_date.month,
                        target_date.day,
                        hour,
                        minute,
                        0,
                        tzinfo=LOCAL_TZ,
                    )

        self.pos = saved_pos

        tok1 = self.peek()
        if tok1.type == TokenType.MODIFIER:
            self.advance()
            modifier = tok1.value

            if self.peek().type == TokenType.DAY:
                day_tok = self.advance()
                target_day = DAYS_MAP[day_tok.value]

                if self.peek().type == TokenType.TIME:
                    time_tok = self.advance()
                    time_parsed = self._parse_time(time_tok.value)
                    if time_parsed:
                        hour, minute = time_parsed

                        days_ahead = target_day - self.now.weekday()
                        if modifier == "next":
                            if days_ahead <= 0:
                                days_ahead += 7
                        else:
                            if days_ahead >= 0:
                                days_ahead -= 7

                        target_date = self.now + timedelta(days=days_ahead)
                        return datetime(
                            target_date.year,
                            target_date.month,
                            target_date.day,
                            hour,
                            minute,
                            0,
                            tzinfo=LOCAL_TZ,
                        )

        self.pos = saved_pos

        if self.peek().type == TokenType.DAY:
            day_tok = self.advance()
            target_day = DAYS_MAP[day_tok.value]

            if self.peek().type == TokenType.TIME:
                time_tok = self.advance()
                time_parsed = self._parse_time(time_tok.value)
                if time_parsed:
                    hour, minute = time_parsed
                    days_ahead = target_day - self.now.weekday()
                    if days_ahead <= 0:
                        days_ahead += 7

                    target_date = self.now + timedelta(days=days_ahead)
                    return datetime(
                        target_date.year,
                        target_date.month,
                        target_date.day,
                        hour,
                        minute,
                        0,
                        tzinfo=LOCAL_TZ,
                    )

        self.pos = saved_pos
        return None

    def _parse_relative_offset(self) -> Optional[datetime]:
        saved_pos = self.pos

        buf = ""
        prev_was_sep = False
        for tok in self.tokens:
            if tok.type == TokenType.EOF:
                break
            if (
                buf
                and not prev_was_sep
                and tok.type not in (TokenType.DATE_SEPARATOR, TokenType.TIME_SEPARATOR)
            ):
                buf += " "
            buf += tok.value
            prev_was_sep = tok.type in (
                TokenType.DATE_SEPARATOR,
                TokenType.TIME_SEPARATOR,
            )

        pattern = r"^([+-]?)(\d+)\s+(days?|weeks?|months?|hours?|minutes?|seconds?)\s*(ago|from now)?$"
        m = re.match(pattern, buf)
        if m:
            sign_str, amount, unit, direction = m.groups()
            amount = int(amount)

            sign = -1 if (sign_str == "-" or direction == "ago") else 1
            amount *= sign

            if unit.startswith("day"):
                return self.now + timedelta(days=amount)
            elif unit.startswith("week"):
                return self.now + timedelta(weeks=amount)
            elif unit.startswith("month"):
                month = self.now.month + amount
                year = self.now.year
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
                        self.now.day,
                        self.now.hour,
                        self.now.minute,
                        self.now.second,
                        tzinfo=LOCAL_TZ,
                    )
                except ValueError:
                    day = min(self.now.day, 28)
                    return datetime(
                        year,
                        month,
                        day,
                        self.now.hour,
                        self.now.minute,
                        self.now.second,
                        tzinfo=LOCAL_TZ,
                    )
            elif unit.startswith("hour"):
                return self.now + timedelta(hours=amount)
            elif unit.startswith("minute"):
                return self.now + timedelta(minutes=amount)
            elif unit.startswith("second"):
                return self.now + timedelta(seconds=amount)

        self.pos = saved_pos
        return None

    def _parse_relative_day(self) -> Optional[datetime]:
        saved_pos = self.pos

        tok1 = self.peek()
        if tok1.type == TokenType.MODIFIER:
            self.advance()
            modifier = tok1.value

            if self.peek().type == TokenType.DAY:
                day_tok = self.advance()
                target_day = DAYS_MAP[day_tok.value]

                days_ahead = target_day - self.now.weekday()
                if modifier == "next":
                    if days_ahead <= 0:
                        days_ahead += 7
                else:
                    if days_ahead >= 0:
                        days_ahead -= 7

                return self.now + timedelta(days=days_ahead)

        self.pos = saved_pos

        tok1 = self.peek()
        if tok1.type == TokenType.DAY:
            day_tok = self.advance()
            target_day = DAYS_MAP[tok1.value]

            days_ahead = target_day - self.now.weekday()
            if days_ahead <= 0:
                days_ahead += 7

            return self.now + timedelta(days=days_ahead)

        self.pos = saved_pos
        return None

    def _parse_ordinal_day(self) -> Optional[datetime]:
        saved_pos = self.pos

        buf = ""
        for tok in self.tokens:
            if tok.type == TokenType.EOF:
                break
            if buf and tok.type not in (
                TokenType.DATE_SEPARATOR,
                TokenType.TIME_SEPARATOR,
            ):
                buf += " "
            buf += tok.value

        pattern = r"^(\d+(?:st|nd|rd|th)?|first|second|third|fourth|fifth)\s+(monday|tuesday|wednesday|thursday|friday|saturday|sunday|mon|tue|wed|thu|fri|sat|sun)\s+(?:of\s+)?(?:(january|february|march|april|may|june|july|august|september|october|november|december|jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\s+)?(\d{4})?$"
        m = re.match(pattern, buf, re.IGNORECASE)
        if m:
            ordinal_str, day_name, month_str, year_str = m.groups()

            ordinal_match = re.match(r"\d+", ordinal_str)
            ordinal = ORDINALS_MAP.get(
                ordinal_str, int(ordinal_match.group()) if ordinal_match else 1
            )
            target_day = DAYS_MAP[day_name]

            month = MONTHS_MAP[month_str.lower()] if month_str else self.now.month
            year = int(year_str) if year_str else self.now.year

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
                            self.now.hour,
                            self.now.minute,
                            self.now.second,
                            tzinfo=LOCAL_TZ,
                        )

            raise DateParseError(f"No {ordinal_str} {day_name} in {month}/{year}")

        pattern = r"^final\s+(monday|tuesday|wednesday|thursday|friday|saturday|sunday|mon|tue|wed|thu|fri|sat|sun)\s+(?:of\s+)?(?:(january|february|march|april|may|june|july|august|september|october|november|december|jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\s+)?(\d{4})?$"
        m = re.match(pattern, buf, re.IGNORECASE)
        if m:
            day_name, month_str, year_str = m.groups()
            target_day = DAYS_MAP[day_name]

            month = MONTHS_MAP[month_str.lower()] if month_str else self.now.month
            year = int(year_str) if year_str else self.now.year

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
                    self.now.hour,
                    self.now.minute,
                    self.now.second,
                    tzinfo=LOCAL_TZ,
                )

            raise DateParseError(f"No {day_name} in {month}/{year}")

        self.pos = saved_pos
        return None

    def _parse_relative_unit(self) -> Optional[datetime]:
        saved_pos = self.pos

        simple_mapping = {
            "today": 0,
            "yesterday": -1,
            "tomorrow": 1,
            "now": 0,
        }

        buf = ""
        for tok in self.tokens:
            if tok.type == TokenType.EOF:
                break
            if buf and tok.type not in (
                TokenType.DATE_SEPARATOR,
                TokenType.TIME_SEPARATOR,
            ):
                buf += " "
            buf += tok.value

        if buf in simple_mapping:
            return self.now + timedelta(days=simple_mapping[buf])

        pattern = r"^(next|last|previous)\s+(week|month|year)$"
        m = re.match(pattern, buf)
        if m:
            direction, unit = m.groups()

            if unit == "week":
                days = 7 if direction == "next" else -7
                return self.now + timedelta(days=days)
            elif unit == "month":
                month = self.now.month + (1 if direction == "next" else -1)
                year = self.now.year
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
                        self.now.day,
                        self.now.hour,
                        self.now.minute,
                        self.now.second,
                        tzinfo=LOCAL_TZ,
                    )
                except ValueError:
                    day = min(self.now.day, 28)
                    return datetime(
                        year,
                        month,
                        day,
                        self.now.hour,
                        self.now.minute,
                        self.now.second,
                        tzinfo=LOCAL_TZ,
                    )
            elif unit == "year":
                year = self.now.year + (1 if direction == "next" else -1)
                try:
                    return datetime(
                        year,
                        self.now.month,
                        self.now.day,
                        self.now.hour,
                        self.now.minute,
                        self.now.second,
                        tzinfo=LOCAL_TZ,
                    )
                except ValueError:
                    day = min(self.now.day, 28)
                    return datetime(
                        year,
                        self.now.month,
                        day,
                        self.now.hour,
                        self.now.minute,
                        self.now.second,
                        tzinfo=LOCAL_TZ,
                    )

        self.pos = saved_pos
        return None


def parse(tokens: list[Token]) -> Optional[datetime]:
    """Parse token stream into datetime."""
    parser = Parser(tokens)
    return parser.parse()


def getdate_with_lexer(buf: str) -> Optional[datetime]:
    """Parse date expression using lexer-based parser."""
    if not buf or not isinstance(buf, str):
        return None

    buf = buf.strip()
    if not buf:
        return None

    tokens = tokenize(buf)
    return parse(tokens)


if __name__ == "__main__":
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
        "2026-03-06",
        "2026-03-06T14:30:00Z",
        "tomorrow 2pm",
        "friday 2pm",
    ]

    for tc in test_cases:
        result = getdate_with_lexer(tc)
        if result:
            print(f"{tc!r:40} -> {result}")
        else:
            print(f"{tc!r:40} -> FAILED")
