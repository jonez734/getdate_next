import unittest
from datetime import datetime, timezone, timedelta
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from getdate import getdate, verify_valid_date_expression


class TestGetDate(unittest.TestCase):
    """Unit tests for getdate module."""

    def test_now(self):
        """Test 'now' returns current time."""
        result = getdate("now")
        self.assertIsNotNone(result)
        self.assertIsNotNone(result.tzinfo)

    def test_today(self):
        """Test 'today' returns today's date."""
        result = getdate("today")
        self.assertIsNotNone(result)
        now = datetime.now()
        self.assertEqual(result.date(), now.date())

    def test_yesterday(self):
        """Test 'yesterday' returns yesterday's date."""
        result = getdate("yesterday")
        self.assertIsNotNone(result)
        now = datetime.now()
        expected = (now - timedelta(days=1)).date()
        self.assertEqual(result.date(), expected)

    def test_tomorrow(self):
        """Test 'tomorrow' returns tomorrow's date."""
        result = getdate("tomorrow")
        self.assertIsNotNone(result)
        now = datetime.now()
        expected = (now + timedelta(days=1)).date()
        self.assertEqual(result.date(), expected)

    def test_plus_days(self):
        """Test +2 days offset."""
        result = getdate("+2 days")
        self.assertIsNotNone(result)
        now = datetime.now()
        expected = (now + timedelta(days=2)).date()
        self.assertEqual(result.date(), expected)

    def test_minus_days(self):
        """Test -3 days offset."""
        result = getdate("-3 days")
        self.assertIsNotNone(result)
        now = datetime.now()
        expected = (now - timedelta(days=3)).date()
        self.assertEqual(result.date(), expected)

    def test_days_ago(self):
        """Test '3 days ago' expression."""
        result = getdate("3 days ago")
        self.assertIsNotNone(result)
        now = datetime.now()
        expected = (now - timedelta(days=3)).date()
        self.assertEqual(result.date(), expected)

    def test_hours_from_now(self):
        """Test '72 hours from now'."""
        result = getdate("72 hours from now")
        self.assertIsNotNone(result)
        now = datetime.now(tz=result.tzinfo)
        expected = now + timedelta(hours=72)
        diff = abs((result - expected).total_seconds())
        self.assertLess(diff, 2)

    def test_next_week(self):
        """Test 'next week'."""
        result = getdate("next week")
        self.assertIsNotNone(result)
        now = datetime.now(tz=result.tzinfo)
        expected = now + timedelta(weeks=1)
        diff = abs((result - expected).total_seconds())
        self.assertLess(diff, 2)

    def test_last_week(self):
        """Test 'last week'."""
        result = getdate("last week")
        self.assertIsNotNone(result)
        now = datetime.now(tz=result.tzinfo)
        expected = now - timedelta(weeks=1)
        diff = abs((result - expected).total_seconds())
        self.assertLess(diff, 2)

    def test_next_month(self):
        """Test 'next month'."""
        result = getdate("next month")
        self.assertIsNotNone(result)

    def test_next_year(self):
        """Test 'next year'."""
        result = getdate("next year")
        self.assertIsNotNone(result)
        now = datetime.now()
        self.assertEqual(result.year, now.year + 1)

    def test_next_thursday(self):
        """Test 'next thursday'."""
        result = getdate("next thursday")
        self.assertIsNotNone(result)
        self.assertEqual(result.weekday(), 3)  # Thursday = 3
        now = datetime.now()
        days_ahead = result.date() - now.date()
        self.assertGreater(days_ahead.days, 0)
        self.assertLessEqual(days_ahead.days, 7)

    def test_last_friday(self):
        """Test 'last friday'."""
        result = getdate("last friday")
        self.assertIsNotNone(result)
        self.assertEqual(result.weekday(), 4)  # Friday = 4
        now = datetime.now()
        days_diff = (now.date() - result.date()).days
        self.assertGreater(days_diff, 0)
        self.assertLessEqual(days_diff, 7)

    def test_ordinal_day(self):
        """Test '2nd wednesday of march 2026'."""
        result = getdate("2nd wednesday of march 2026")
        self.assertIsNotNone(result)
        self.assertEqual(result.year, 2026)
        self.assertEqual(result.month, 3)
        self.assertEqual(result.weekday(), 2)  # Wednesday = 2

    def test_ordinal_day_no_year(self):
        """Test '1st monday of march'."""
        result = getdate("1st monday of march")
        self.assertIsNotNone(result)
        self.assertEqual(result.month, 3)
        self.assertEqual(result.weekday(), 0)  # Monday = 0

    def test_final_friday(self):
        """Test 'final friday of march 2026'."""
        result = getdate("final friday of march 2026")
        self.assertIsNotNone(result)
        self.assertEqual(result.year, 2026)
        self.assertEqual(result.month, 3)
        self.assertEqual(result.weekday(), 4)  # Friday = 4

    def test_iso_date(self):
        """Test ISO date '2026-03-06'."""
        result = getdate("2026-03-06")
        self.assertIsNotNone(result)
        self.assertEqual(result.year, 2026)
        self.assertEqual(result.month, 3)
        self.assertEqual(result.day, 6)

    def test_iso8601_with_utc_z(self):
        """Test ISO8601 with Z suffix (UTC)."""
        result = getdate("2026-03-06T14:30:00Z")
        self.assertIsNotNone(result)
        self.assertEqual(result.year, 2026)
        self.assertEqual(result.month, 3)
        self.assertEqual(result.day, 6)
        self.assertEqual(result.hour, 14)
        self.assertEqual(result.minute, 30)
        self.assertIsNotNone(result.tzinfo)

    def test_iso8601_with_plus08_offset(self):
        """Test ISO8601 with +08:00 offset (e.g., LA/Australia)."""
        result = getdate("2026-03-06T14:30:00+08:00")
        self.assertIsNotNone(result)
        self.assertEqual(result.year, 2026)
        self.assertEqual(result.month, 3)
        self.assertEqual(result.day, 6)
        self.assertEqual(result.hour, 14)  # preserved, not converted
        self.assertEqual(result.minute, 30)
        self.assertIsNotNone(result.tzinfo)
        # Verify offset is +08:00
        offset = result.utcoffset()
        self.assertEqual(offset, timedelta(hours=8))

    def test_iso8601_with_minus05_offset(self):
        """Test ISO8601 with -05:00 offset (e.g., EST)."""
        result = getdate("2026-03-06T14:30:00-05:00")
        self.assertIsNotNone(result)
        self.assertEqual(result.hour, 14)  # preserved
        self.assertIsNotNone(result.tzinfo)
        offset = result.utcoffset()
        self.assertEqual(offset, timedelta(hours=-5))

    def test_iso8601_with_plus08_no_colon(self):
        """Test ISO8601 with +0800 (no colon)."""
        result = getdate("2026-03-06T14:30:00+0800")
        self.assertIsNotNone(result)
        self.assertEqual(result.hour, 14)
        offset = result.utcoffset()
        self.assertEqual(offset, timedelta(hours=8))

    def test_iso8601_preserves_hour_not_converted(self):
        """Test that hour is preserved, not converted to local timezone."""
        result = getdate("2026-03-06T10:00:00+08:00")
        self.assertIsNotNone(result)
        # The hour should be 10, not converted to local time
        self.assertEqual(result.hour, 10)
        self.assertEqual(result.minute, 0)

    def test_us_date_with_time(self):
        """Test US date with time '3/5/2026 21:45'."""
        result = getdate("3/5/2026 21:45")
        self.assertIsNotNone(result)
        self.assertEqual(result.month, 3)
        self.assertEqual(result.day, 5)
        self.assertEqual(result.year, 2026)
        self.assertEqual(result.hour, 21)
        self.assertEqual(result.minute, 45)

    def test_us_date_with_12hour_pm(self):
        """Test US date with 12-hour PM time '3/5/2026 9:45p'."""
        result = getdate("3/5/2026 9:45p")
        self.assertIsNotNone(result)
        self.assertEqual(result.hour, 21)  # 9 PM

    def test_us_date_only(self):
        """Test US date only '03/06/2026'."""
        result = getdate("03/06/2026")
        self.assertIsNotNone(result)
        self.assertEqual(result.month, 3)
        self.assertEqual(result.day, 6)
        self.assertEqual(result.year, 2026)

    def test_compact_format(self):
        """Test compact format '202603062145'."""
        result = getdate("202603062145")
        self.assertIsNotNone(result)
        self.assertEqual(result.year, 2026)
        self.assertEqual(result.month, 3)
        self.assertEqual(result.day, 6)
        self.assertEqual(result.hour, 21)
        self.assertEqual(result.minute, 45)

    def test_verify_valid_date_expression_true(self):
        """Test verify_valid_date_expression with valid input."""
        self.assertTrue(verify_valid_date_expression("now"))
        self.assertTrue(verify_valid_date_expression("next friday"))
        self.assertTrue(verify_valid_date_expression("2026-03-06"))

    def test_verify_valid_date_expression_false(self):
        """Test verify_valid_date_expression with invalid input."""
        self.assertFalse(verify_valid_date_expression("invalid garbage"))
        self.assertFalse(verify_valid_date_expression("not a date"))
        self.assertFalse(verify_valid_date_expression(""))

    def test_returns_none_for_invalid(self):
        """Test that invalid input returns None."""
        result = getdate("invalid garbage")
        self.assertIsNone(result)

    def test_returns_timezone_aware(self):
        """Test that all results are timezone-aware."""
        test_cases = [
            "now",
            "today",
            "tomorrow",
            "+2 days",
            "next week",
            "next thursday",
            "2026-03-06",
        ]
        for tc in test_cases:
            result = getdate(tc)
            if result:
                self.assertIsNotNone(result.tzinfo, f"{tc} should be timezone-aware")

    def test_null_input(self):
        """Test null/None input returns None."""
        self.assertIsNone(getdate(None))
        self.assertIsNone(getdate(""))

    def test_invalid_returns_none(self):
        """Test that invalid expressions return None, not raise exception."""
        self.assertIsNone(getdate("not a date"))
        self.assertIsNone(getdate("abcdef"))
        self.assertIsNone(getdate("32nd day of jamuary"))


class TestTimezonePreservation(unittest.TestCase):
    """Test that timezone offsets are preserved correctly."""

    def test_plus08_preserves_exact_hour(self):
        """Ensure +08:00 keeps the input hour exactly."""
        result = getdate("2026-03-06T14:30:00+08:00")
        self.assertEqual(result.hour, 14)
        self.assertEqual(result.minute, 30)

    def test_minus05_preserves_exact_hour(self):
        """Ensure -05:00 keeps the input hour exactly."""
        result = getdate("2026-03-06T09:30:00-05:00")
        self.assertEqual(result.hour, 9)
        self.assertEqual(result.minute, 30)

    def test_utc_z_is_utc(self):
        """Ensure Z suffix results in UTC timezone."""
        result = getdate("2026-03-06T14:30:00Z")
        self.assertEqual(result.tzinfo, timezone.utc)

    def test_explicit_offset_not_converted(self):
        """Verify explicit offsets are stored, not converted."""
        result = getdate("2026-03-06T00:00:00+12:00")
        # Should be noon in UTC
        self.assertEqual(result.hour, 0)
        offset = result.utcoffset()
        self.assertEqual(offset, timedelta(hours=12))


if __name__ == "__main__":
    unittest.main(verbosity=2)
