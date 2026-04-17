"""
lexer.py - Tokenizer for natural language date expressions.

Provides tokenization of date strings into a stream of tokens
for parsing by the datetime parser.
"""

from enum import Enum, auto
from dataclasses import dataclass
from typing import Optional


class TokenType(Enum):
    NUMBER = auto()
    WORD = auto()
    MODIFIER = auto()
    TIME = auto()
    OFFSET = auto()
    ORDINAL = auto()
    DAY = auto()
    MONTH = auto()
    UNIT = auto()
    DATE_SEPARATOR = auto()
    TIME_SEPARATOR = auto()
    TIMEZONE = auto()
    COMMA = auto()
    UNIX = auto()
    AT = auto()
    EOF = auto()


@dataclass
class Token:
    type: TokenType
    value: str
    position: int


MODIFIERS = {"next", "last", "previous"}
OFFSETS = {"ago", "from", "now", "until", "since"}
UNITS = {
    "day",
    "days",
    "week",
    "weeks",
    "month",
    "months",
    "year",
    "years",
    "hour",
    "hours",
    "minute",
    "minutes",
    "second",
    "seconds",
}

DAYS = {
    "monday",
    "tuesday",
    "wednesday",
    "thursday",
    "friday",
    "saturday",
    "sunday",
    "mon",
    "tue",
    "wed",
    "thu",
    "fri",
    "sat",
    "sun",
}

MONTHS = {
    "january",
    "february",
    "march",
    "april",
    "may",
    "june",
    "july",
    "august",
    "september",
    "october",
    "november",
    "december",
    "jan",
    "feb",
    "mar",
    "apr",
    "jun",
    "jul",
    "aug",
    "sep",
    "oct",
    "nov",
    "dec",
}

TIME_WORDS = {"noon", "midday", "midnight", "night", "morning", "evening", "am", "pm", "a", "p", "of"}

ORDINALS = {
    "first",
    "second",
    "third",
    "fourth",
    "fifth",
    "sixth",
    "seventh",
    "eighth",
    "ninth",
    "tenth",
    "eleventh",
    "twelfth",
    "1st",
    "2nd",
    "3rd",
    "4th",
    "5th",
    "6th",
    "7th",
    "8th",
    "9th",
    "10th",
    "11th",
    "12th",
}

from .timezone_data import TIMEZONE_ABBREV_OFFSET

TIMEZONES = set(TIMEZONE_ABBREV_OFFSET.keys())


class TokenizerError(Exception):
    """Raised when tokenization fails."""

    pass


class Tokenizer:
    def __init__(self, buf: str):
        self.buf = buf.strip().lower()
        self.pos = 0
        self.tokens: list[Token] = []
        self.prev_token_type: Optional[TokenType] = None

    def tokenize(self) -> list[Token]:
        """Tokenize the input string."""
        while self.pos < len(self.buf):
            self._skip_whitespace()
            if self.pos >= len(self.buf):
                break

            token = self._next_token()
            if token:
                self.tokens.append(token)
                self.prev_token_type = token.type

        self.tokens.append(Token(TokenType.EOF, "", self.pos))
        return self.tokens

    def _skip_whitespace(self) -> None:
        while self.pos < len(self.buf) and self.buf[self.pos].isspace():
            self.pos += 1

    def _next_token(self) -> Optional[Token]:
        char = self.buf[self.pos]

        if char.isdigit():
            return self._tokenize_number()
        if char.isalpha():
            return self._tokenize_word()
        if char in "-/+":
            return self._tokenize_separator()
        if char in ":":
            return self._tokenize_time_separator()
        if char == ",":
            return self._tokenize_comma()

        self.pos += 1
        return None

    def _tokenize_comma(self) -> Token:
        char = self.buf[self.pos]
        self.pos += 1
        return Token(TokenType.COMMA, char, self.pos - 1)

    def _tokenize_number(self) -> Token:
        start = self.pos
        while self.pos < len(self.buf) and self.buf[self.pos].isdigit():
            self.pos += 1

        value = self.buf[start : self.pos]

        if self.pos < len(self.buf) and self.buf[self.pos] in "stndrth":
            suffix = ""
            while self.pos < len(self.buf) and self.buf[self.pos] in "stndrth":
                suffix += self.buf[self.pos]
                self.pos += 1
            value = value + suffix
            if value in ORDINALS:
                return Token(TokenType.ORDINAL, value, start)
            return Token(TokenType.NUMBER, value, start)

        if self.pos < len(self.buf):
            next_char = self.buf[self.pos].lower()
            if (
                next_char in "ap"
                or self.buf[self.pos :].startswith("am")
                or self.buf[self.pos :].startswith("pm")
            ):
                if len(value) >= 3 and len(value) <= 4 and value.isdigit():
                    return Token(TokenType.NUMBER, value, start)
                ampm = ""
                while self.pos < len(self.buf) and self.buf[self.pos].isalpha():
                    ampm += self.buf[self.pos]
                    self.pos += 1
                return Token(TokenType.TIME, value + ampm, start)

            if next_char == ":":
                time_val = value
                while self.pos < len(self.buf) and self.buf[self.pos] in "0123456789:":
                    time_val += self.buf[self.pos]
                    self.pos += 1
                if self.pos < len(self.buf) and self.buf[self.pos].lower() in "ap":
                    ampm = ""
                    while self.pos < len(self.buf) and self.buf[self.pos].isalpha():
                        ampm += self.buf[self.pos]
                        self.pos += 1
                    return Token(TokenType.TIME, time_val + ampm, start)
                return Token(TokenType.TIME, time_val, start)

        if len(value) == 10 and value.isdigit():
            return Token(TokenType.UNIX, value, start)

        return Token(TokenType.NUMBER, value, start)

    def _tokenize_word(self) -> Token:
        start = self.pos
        while self.pos < len(self.buf) and self.buf[self.pos].isalnum():
            self.pos += 1

        value = self.buf[start : self.pos]

        if value in MODIFIERS:
            return Token(TokenType.MODIFIER, value, start)
        if value in DAYS:
            return Token(TokenType.DAY, value, start)
        if value in MONTHS:
            return Token(TokenType.MONTH, value, start)
        if value in TIME_WORDS:
            return Token(TokenType.TIME, value, start)
        if value in UNITS:
            return Token(TokenType.UNIT, value, start)
        if value in OFFSETS:
            return Token(TokenType.OFFSET, value, start)
        if value in ORDINALS:
            return Token(TokenType.ORDINAL, value, start)
        if value in TIMEZONES:
            return Token(TokenType.TIMEZONE, value, start)
        if value == "at":
            return Token(TokenType.AT, value, start)

        return Token(TokenType.WORD, value, start)

    def _tokenize_separator(self) -> Token:
        char = self.buf[self.pos]
        self.pos += 1

        if char in "+-" and self.prev_token_type == TokenType.TIME:
            tz_val = char
            while self.pos < len(self.buf) and (self.buf[self.pos].isdigit() or self.buf[self.pos] == ":"):
                tz_val += self.buf[self.pos]
                self.pos += 1
            return Token(TokenType.TIMEZONE, tz_val, self.pos - len(tz_val))

        return Token(TokenType.DATE_SEPARATOR, char, self.pos - 1)

    def _tokenize_time_separator(self) -> Token:
        char = self.buf[self.pos]
        self.pos += 1
        return Token(TokenType.TIME_SEPARATOR, char, self.pos - 1)


def tokenize(buf: str) -> list[Token]:
    """
    Tokenize a date expression string.

    Args:
        buf: Date expression string

    Returns:
        List of tokens
    """
    if not buf or not isinstance(buf, str):
        return []

    tokenizer = Tokenizer(buf)
    return tokenizer.tokenize()


if __name__ == "__main__":
    test_cases = [
        "next friday 2pm",
        "2nd wednesday of march 2026",
        "+2 days",
        "3 days ago",
        "2026-03-06T14:30:00Z",
        "tomorrow noon",
        "next week",
        "final friday of march",
    ]

    for tc in test_cases:
        tokens = tokenize(tc)
        print(f"{tc!r}:")
        for tok in tokens:
            if tok.type == TokenType.EOF:
                break
            print(f"  {tok.type.name:15} {tok.value!r:20}")
        print()
