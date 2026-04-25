"""
validation.py - Date and time validation functions.

Provides validation functions for year, month, day, hour, minute, and second components.
"""

import calendar
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class ValidationError:
    """Represents a single validation error."""
    field: str
    value: any
    message: str


@dataclass
class ValidationResult:
    """Result of validating a date/time expression."""
    valid: bool
    errors: List[ValidationError] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    @property
    def error_messages(self) -> List[str]:
        return [e.message for e in self.errors]


def validate_year(year: int) -> Optional[ValidationError]:
    """Validate year is in reasonable range."""
    if year < 1900:
        return ValidationError("year", year, f"year {year} is too early (minimum 1900)")
    if year > 2100:
        return ValidationError("year", year, f"year {year} is too far in the future (maximum 2100)")
    return None


def validate_month(month: int) -> Optional[ValidationError]:
    """Validate month is 1-12."""
    if month < 1:
        return ValidationError("month", month, f"month {month} is invalid (must be 1-12)")
    if month > 12:
        return ValidationError("month", month, f"month {month} is invalid (must be 1-12)")
    return None


def validate_day(year: int, month: int, day: int) -> Optional[ValidationError]:
    """Validate day is valid for the given month and year."""
    if day < 1:
        return ValidationError("day", day, f"day {day} is invalid (must be 1-31)")

    if month < 1 or month > 12:
        return ValidationError("day", day, f"day {day} is invalid (month {month} is out of range)")

    max_days = calendar.monthrange(year, month)[1]
    if day > max_days:
        month_name = calendar.month_name[month]
        return ValidationError(
            "day", day,
            f"{month_name} {day} does not exist (maximum {max_days} days in {month_name} {year})"
        )

    return None


def validate_hour(hour: int) -> Optional[ValidationError]:
    """Validate hour is 0-23."""
    if hour < 0:
        return ValidationError("hour", hour, f"hour {hour} is invalid (must be 0-23)")
    if hour > 23:
        return ValidationError("hour", hour, f"hour {hour} is invalid (must be 0-23)")
    return None


def validate_minute(minute: int) -> Optional[ValidationError]:
    """Validate minute is 0-59."""
    if minute < 0:
        return ValidationError("minute", minute, f"minute {minute} is invalid (must be 0-59)")
    if minute > 59:
        return ValidationError("minute", minute, f"minute {minute} is invalid (must be 0-59)")
    return None


def validate_second(second: int) -> Optional[ValidationError]:
    """Validate second is 0-59."""
    if second < 0:
        return ValidationError("second", second, f"second {second} is invalid (must be 0-59)")
    if second > 59:
        return ValidationError("second", second, f"second {second} is invalid (must be 0-59)")
    return None


def validate_time(hour: int, minute: int, second: int = 0) -> List[ValidationError]:
    """Validate all time components."""
    errors = []
    err = validate_hour(hour)
    if err:
        errors.append(err)
    err = validate_minute(minute)
    if err:
        errors.append(err)
    err = validate_second(second)
    if err:
        errors.append(err)
    return errors


def validate_date(year: int, month: int, day: int) -> List[ValidationError]:
    """Validate all date components."""
    errors = []
    err = validate_year(year)
    if err:
        errors.append(err)
    err = validate_month(month)
    if err:
        errors.append(err)
    err = validate_day(year, month, day)
    if err:
        errors.append(err)
    return errors


def validate_datetime(
    year: int, month: int, day: int,
    hour: int = 0, minute: int = 0, second: int = 0
) -> ValidationResult:
    """Validate all date and time components."""
    errors = []
    errors.extend(validate_date(year, month, day))
    errors.extend(validate_time(hour, minute, second))

    return ValidationResult(
        valid=len(errors) == 0,
        errors=errors
    )