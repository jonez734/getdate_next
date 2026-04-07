# datetime expression evaluator returns a timezone aware datetime.datetime object

## Status

**IMPLEMENTED** - Core functionality complete in `getdate.py` and PHP version in `php/`

## PHP Implementation

A full PHP port is available in the `php/` directory with feature parity to the Python version.

### PHP Usage

```php
use GetdateNext\Getdate;

// Parse a date expression - returns DateTimeImmutable
$result = Getdate::getdate("next friday");
echo $result->format('Y-m-d H:i:s');  // 2026-04-10 14:00:00

// Returns DateInterval for "days until/since" expressions
$result = Getdate::getdate("days until 2nd wednesday april 2026");
echo $result->format('%a days');  // 4 days

// Unix timestamp variant
$timestamp = Getdate::getdateTimestamp("next friday");

// Verify a date expression
if (Getdate::verifyValidDateExpression("tomorrow")) {
    echo "Valid!";
}
```

### PHP Running Tests

```bash
cd php
composer install
./vendor/bin/phpunit tests/
```

## details
- accept singular or plural for components like "day", "week", "month", etc

- if a required component is missing, fill in with current date/time
  components

- if any component is missing, use the current value for that component (like
  missing year, substitute 2026)
- if a complete datetime cannot be constructed, be clear about what the
  error(s) are
- add a --debug option to the demo that will show each component and it's value
- return a timezone aware datetime.datetime object
- the parser must be easily extensible to accomodate new formats
- the code is to be clean, robust, and free of any lint warnings or errors
- prefer to use only stdlib modules, but can accept a couple of `pip
  install`s if required.

## Implemented Formats

### Relative Expressions
- `now`, `today`, `yesterday`, `tomorrow`
- `next week`, `last week`
- `next month`, `next year`
- `next thursday`, `last friday` (and other day names)
- `1st monday of march`, `2nd wednesday of march 2026`
- `final friday of march 2026`
- `days until 2nd wednesday of march 2026` (returns timedelta)
- `days until final friday of may 2026` (returns timedelta)
- `days since 2nd wednesday of march 2026` (returns timedelta)

### Offset Expressions
- `+2 days`, `-3 days`
- `3 days ago`, `72 hours from now`, `48 hours ago`
- `+2 weeks`
- `+/-72 hours`

### Numeric Formats
- ISO 8601: `2026-03-06`, `2026-03-06T14:30:00Z`
- US Date: `3/5/2026 21:45`, `3/5/2026 9:45p`, `03/06/2026`
- Compact: `202603062145` (YYYYMMDDHHMM)

## examples of input (tested):

- days until 2nd wednesday april 2026 ✅
- days until final friday of may 2026 ✅
- days since 2nd wednesday march 2026 ✅
- 2nd wednesday of march 2026 ✅
- 2nd wednesday next month 2026 ❌ (not implemented)
- 202603062145 ✅

- 3/5/2026 21:45 ✅
- 3/5/2026 9:45p ✅
- 2026-03-05 ✅
- ISO 8601: 2026-03-06T14:30:00Z ✅
- Standard Date (US): 03/06/2026 ✅
- Year-Month-Day: 2026-03-06 ✅

- next thursday at noon ❌ (not implemented)
- last friday ✅
- final friday of march 2026 ✅
- 1st monday of march ✅
- next week ✅
- next month ✅
- 3 days ago ✅
- 72 hours from now ✅
- 48 hours ago ✅
- yesterday ✅
- tomorrow ✅
- +2 weeks ✅

## Not Yet Implemented

- Fri Mar  6 09:45:35 PM EST 2026 (RFC 822)
- Full Date & Time: Monday, March 06, 2026 10:15 AM
- Standard Date (International): 06/03/2026 or 06-Mar-2026
- Time (24-hour): 14:30:00
- Time (12-hour): 02:30:00 PM
- Time (short 12-hour): 0230p
- RFC 3339: 2026-03-06 21:54:30+00:00
- RFC 1123 / RFC 822: Fri, 06 Mar 2026 21:54:30 GMT
- Unix Timestamp: 1741305270

## Architecture

```
getdate.py       - Main entry point (getdate(), verify_valid_date_expression())
_parser.py       - Parser functions (extensible)
```

Each format has its own parser function that can be added to the `parsers` list
in `getdate()`. This makes the system easily extensible for new formats.

## Usage

```python
from getdate import getdate, verify_valid_date_expression

# Parse a date expression
result = getdate("next friday")
print(result)  # 2026-03-13 20:51:15.080946-05:00

# Validate a date expression
if verify_valid_date_expression("tomorrow"):
    print("Valid!")
```

## Running Tests

```bash
python getdate.py                    # Run all test cases
python getdate.py "next week"        # Test specific expression
```
