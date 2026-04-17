import unittest
from datetime import datetime, timezone, timedelta
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))
from getdate_next.getdate import getdate, verify_valid_date_expression


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

    def test_tomorrow_2pm(self):
        """Test 'tomorrow 2pm' returns tomorrow at 2:00 PM."""
        result = getdate("tomorrow 2pm")
        self.assertIsNotNone(result)
        expected = (datetime.now() + timedelta(days=1)).date()
        self.assertEqual(result.date(), expected)
        self.assertEqual(result.hour, 14)
        self.assertEqual(result.minute, 0)

    def test_yesterday_9am(self):
        """Test 'yesterday 9am' returns yesterday at 9:00 AM."""
        result = getdate("yesterday 9am")
        self.assertIsNotNone(result)
        expected = (datetime.now() - timedelta(days=1)).date()
        self.assertEqual(result.date(), expected)
        self.assertEqual(result.hour, 9)
        self.assertEqual(result.minute, 0)

    def test_today_5pm(self):
        """Test 'today 5pm' returns today at 5:00 PM."""
        result = getdate("today 5pm")
        self.assertIsNotNone(result)
        now = datetime.now()
        self.assertEqual(result.date(), now.date())
        self.assertEqual(result.hour, 17)
        self.assertEqual(result.minute, 0)

    def test_friday_2pm(self):
        """Test 'friday 2pm' returns next Friday at 2:00 PM."""
        result = getdate("friday 2pm")
        self.assertIsNotNone(result)
        self.assertEqual(result.weekday(), 4)  # Friday = 4
        self.assertEqual(result.hour, 14)
        self.assertEqual(result.minute, 0)

    def test_thursday_330pm(self):
        """Test 'thursday 3:30pm' returns next Thursday at 3:30 PM."""
        result = getdate("thursday 3:30pm")
        self.assertIsNotNone(result)
        self.assertEqual(result.weekday(), 3)  # Thursday = 3
        self.assertEqual(result.hour, 15)
        self.assertEqual(result.minute, 30)

    def test_next_thursday_2pm(self):
        """Test 'next thursday 2pm'."""
        result = getdate("next thursday 2pm")
        self.assertIsNotNone(result)
        self.assertEqual(result.weekday(), 3)  # Thursday = 3
        self.assertEqual(result.hour, 14)
        self.assertEqual(result.minute, 0)

    def test_tomorrow_noon(self):
        """Test 'tomorrow noon' returns tomorrow at 12:00 PM."""
        result = getdate("tomorrow noon")
        self.assertIsNotNone(result)
        expected = (datetime.now() + timedelta(days=1)).date()
        self.assertEqual(result.date(), expected)
        self.assertEqual(result.hour, 12)
        self.assertEqual(result.minute, 0)

    def test_yesterday_midnight(self):
        """Test 'yesterday midnight' returns yesterday at 12:00 AM."""
        result = getdate("yesterday midnight")
        self.assertIsNotNone(result)
        expected = (datetime.now() - timedelta(days=1)).date()
        self.assertEqual(result.date(), expected)
        self.assertEqual(result.hour, 0)
        self.assertEqual(result.minute, 0)

    def test_next_friday_2pm(self):
        """Test 'next friday 2pm'."""
        result = getdate("next friday 2pm")
        print(f"Result: {result}")
        self.assertIsNotNone(result)
        self.assertEqual(result.weekday(), 4)  # Friday = 4
        self.assertEqual(result.hour, 14)
        self.assertEqual(result.minute, 0)

    def test_last_friday_2pm(self):
        """Test 'last friday 2pm'."""
        result = getdate("last friday 2pm")
        print(f"Result: {result}")
        self.assertIsNotNone(result)
        self.assertEqual(result.weekday(), 4)  # Friday = 4
        self.assertEqual(result.hour, 14)
        self.assertEqual(result.minute, 0)

    def test_days_until_ordinal(self):
        """Test 'days until 2nd wednesday' returns timedelta."""
        now = datetime.now()
        future_year = now.year if now.month < 11 else now.year + 1
        future_month = now.month + 1 if now.month < 12 else 1
        month_name = ["january", "february", "march", "april", "may", "june",
                      "july", "august", "september", "october", "november", "december"][future_month - 1]
        result = getdate(f"days until 2nd wednesday of {month_name} {future_year}")
        self.assertIsNotNone(result)
        self.assertIsInstance(result, timedelta)
        self.assertGreater(result.days, 0)

    def test_days_until_final(self):
        """Test 'days until final friday' returns timedelta."""
        now = datetime.now()
        future_year = now.year if now.month < 11 else now.year + 1
        result = getdate(f"days until final friday of december {future_year}")
        self.assertIsNotNone(result)
        self.assertIsInstance(result, timedelta)
        self.assertGreater(result.days, 0)

    def test_days_until_simple(self):
        """Test 'days until next friday' returns timedelta."""
        result = getdate("days until next friday")
        self.assertIsNotNone(result)
        self.assertIsInstance(result, timedelta)
        self.assertGreater(result.days, 0)

    def test_days_since_past(self):
        """Test 'days since' with a past date returns timedelta."""
        now = datetime.now()
        past_year = now.year - 1
        result = getdate(f"days since 2nd wednesday march {past_year}")
        self.assertIsNotNone(result)
        self.assertIsInstance(result, timedelta)
        self.assertGreater(result.days, 0)

    def test_day_until_singular(self):
        """Test 'day until' (singular) works."""
        result = getdate("day until next friday")
        self.assertIsNotNone(result)
        self.assertIsInstance(result, timedelta)
        self.assertGreater(result.days, 0)


class TestDatelineCrossing(unittest.TestCase):
    """Test parsing dates with timezones that cross the International Date Line.
    
    The International Date Line is at approximately +12:00 UTC.
    Timezones east of this (like +14:00) are "ahead" of UTC by more than a day
    compared to timezones west of it.
    """

    def test_plus14_timezone_parsing(self):
        """Test +14:00 timezone (Kiritimati/Line Islands, east of dateline).
        
        +14:00 is the furthest timezone ahead of UTC, 2 hours ahead of +12:00.
        """
        result = getdate("2026-04-03T23:00:00+14:00")
        self.assertIsNotNone(result)
        self.assertEqual(result.hour, 23)
        self.assertEqual(result.minute, 0)
        self.assertEqual(result.day, 3)
        self.assertEqual(result.month, 4)
        self.assertEqual(result.year, 2026)
        offset = result.utcoffset()
        self.assertEqual(offset, timedelta(hours=14))

    def test_minus12_timezone_parsing(self):
        """Test -12:00 timezone (Baker Island, west of dateline).
        
        -12:00 is the furthest timezone behind UTC, on the western side of the dateline.
        """
        result = getdate("2026-04-03T02:00:00-12:00")
        self.assertIsNotNone(result)
        self.assertEqual(result.hour, 2)
        self.assertEqual(result.minute, 0)
        self.assertEqual(result.day, 3)
        self.assertEqual(result.month, 4)
        self.assertEqual(result.year, 2026)
        offset = result.utcoffset()
        self.assertEqual(offset, timedelta(hours=-12))

    def test_plus12_timezone_at_datelien(self):
        """Test +12:00 timezone (near International Date Line)."""
        result = getdate("2026-04-03T22:00:00+12:00")
        self.assertIsNotNone(result)
        self.assertEqual(result.hour, 22)
        self.assertEqual(result.day, 3)
        offset = result.utcoffset()
        self.assertEqual(offset, timedelta(hours=12))

    def test_end_of_month_plus14(self):
        """Test +14:00 timezone at end of month."""
        result = getdate("2026-04-30T22:00:00+14:00")
        self.assertIsNotNone(result)
        self.assertEqual(result.month, 4)
        self.assertEqual(result.day, 30)
        self.assertEqual(result.hour, 22)

    def test_year_boundary_plus14(self):
        """Test +14:00 timezone at year boundary."""
        result = getdate("2026-12-31T22:00:00+14:00")
        self.assertIsNotNone(result)
        self.assertEqual(result.year, 2026)
        self.assertEqual(result.month, 12)
        self.assertEqual(result.day, 31)
        self.assertEqual(result.hour, 22)

    def test_year_boundary_minus12(self):
        """Test -12:00 timezone at year boundary."""
        result = getdate("2026-12-31T02:00:00-12:00")
        self.assertIsNotNone(result)
        self.assertEqual(result.year, 2026)
        self.assertEqual(result.month, 12)
        self.assertEqual(result.day, 31)
        self.assertEqual(result.hour, 2)


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


class TestNewFormats(unittest.TestCase):
    """Tests for newly implemented formats from SPEC.md."""

    def test_ordinal_with_relative(self):
        """Test '2nd wednesday next month 2026' - ordinal + relative unit."""
        result = getdate("2nd wednesday next month 2026")
        self.assertIsNotNone(result)
        self.assertEqual(result.year, 2026)
        self.assertEqual(result.weekday(), 2)  # Wednesday
        self.assertEqual(result.month, 5)  # May (next month from April)

    def test_day_at_special_time(self):
        """Test 'next thursday at noon' - day + at + time."""
        result = getdate("next thursday at noon")
        self.assertIsNotNone(result)
        self.assertEqual(result.weekday(), 3)  # Thursday
        self.assertEqual(result.hour, 12)
        self.assertEqual(result.minute, 0)

    def test_rfc822(self):
        """Test RFC 822 format 'Fri Mar 6 09:45:35 PM EST 2026'."""
        result = getdate("Fri Mar 6 09:45:35 PM EST 2026")
        self.assertIsNotNone(result)
        self.assertEqual(result.year, 2026)
        self.assertEqual(result.month, 3)
        self.assertEqual(result.day, 6)
        self.assertEqual(result.hour, 21)
        self.assertEqual(result.minute, 45)
        self.assertEqual(result.second, 35)
        offset = result.utcoffset()
        self.assertEqual(offset, timedelta(hours=-5))

    def test_full_date_time(self):
        """Test 'Monday, March 06, 2026 10:15 AM'."""
        result = getdate("Monday, March 06, 2026 10:15 AM")
        self.assertIsNotNone(result)
        self.assertEqual(result.year, 2026)
        self.assertEqual(result.month, 3)
        self.assertEqual(result.day, 6)
        self.assertEqual(result.hour, 10)
        self.assertEqual(result.minute, 15)

    def test_international_date_slash(self):
        """Test international date '13/03/2026' (DD/MM/YYYY) - unambiguous."""
        result = getdate("13/03/2026")
        self.assertIsNotNone(result)
        self.assertEqual(result.year, 2026)
        self.assertEqual(result.month, 3)
        self.assertEqual(result.day, 13)

    def test_international_date_dash(self):
        """Test international date '06-Mar-2026'."""
        result = getdate("06-Mar-2026")
        self.assertIsNotNone(result)
        self.assertEqual(result.year, 2026)
        self.assertEqual(result.month, 3)
        self.assertEqual(result.day, 6)

    def test_24hour_time(self):
        """Test 24-hour time '14:30:00' returns today's date."""
        result = getdate("14:30:00")
        self.assertIsNotNone(result)
        now = datetime.now()
        self.assertEqual(result.date(), now.date())
        self.assertEqual(result.hour, 14)
        self.assertEqual(result.minute, 30)
        self.assertEqual(result.second, 0)

    def test_12hour_time(self):
        """Test 12-hour time '02:30:00 PM' returns today's date."""
        result = getdate("02:30:00 PM")
        self.assertIsNotNone(result)
        now = datetime.now()
        self.assertEqual(result.date(), now.date())
        self.assertEqual(result.hour, 14)
        self.assertEqual(result.minute, 30)

    def test_short_12hour_time(self):
        """Test short 12-hour time '0230p' returns today's date."""
        result = getdate("0230p")
        self.assertIsNotNone(result)
        now = datetime.now()
        self.assertEqual(result.date(), now.date())
        self.assertEqual(result.hour, 14)
        self.assertEqual(result.minute, 30)

    def test_rfc3339(self):
        """Test RFC 3339 format '2026-03-06 21:54:30+00:00'."""
        result = getdate("2026-03-06 21:54:30+00:00")
        self.assertIsNotNone(result)
        self.assertEqual(result.year, 2026)
        self.assertEqual(result.month, 3)
        self.assertEqual(result.day, 6)
        self.assertEqual(result.hour, 21)
        self.assertEqual(result.minute, 54)
        self.assertEqual(result.second, 30)
        offset = result.utcoffset()
        self.assertEqual(offset, timedelta(hours=0))

    def test_rfc1123(self):
        """Test RFC 1123 format 'Fri, 06 Mar 2026 21:54:30 GMT'."""
        result = getdate("Fri, 06 Mar 2026 21:54:30 GMT")
        self.assertIsNotNone(result)
        self.assertEqual(result.year, 2026)
        self.assertEqual(result.month, 3)
        self.assertEqual(result.day, 6)
        self.assertEqual(result.hour, 21)
        self.assertEqual(result.minute, 54)
        self.assertEqual(result.second, 30)
        self.assertEqual(result.tzinfo, timezone.utc)

    def test_unix_timestamp(self):
        """Test Unix timestamp '1741305270'."""
        result = getdate("1741305270")
        self.assertIsNotNone(result)
        # 1741305270 = March 6, 2026 19:54:30 UTC
        self.assertEqual(result.year, 2025)
        self.assertEqual(result.month, 3)
        self.assertEqual(result.day, 6)


if __name__ == "__main__":
    unittest.main(verbosity=2)
