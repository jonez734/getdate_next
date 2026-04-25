# datetime expression evaluator returns a timezone aware datetime.datetime object

## Status

**IMPLEMENTED** - Core functionality complete in `getdate.py`, PHP version in `php/`, and Perl version in `perl/`

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

## Perl Implementation

A full Perl port is available in the `perl/` directory with feature parity to the Python version. Uses core modules only (no external dependencies).

### Perl Usage

```perl
use Getdate::Getdate;

# Parse a date expression - returns Getdate::DateTime
my $result = Getdate::Getdate::getdate("next friday");
print $result->format("%Y-%m-%d %H:%M:%S");  # 2026-04-23 22:05:00

# Returns Getdate::DateInterval for "days until/since" expressions
my $result = Getdate::Getdate::getdate("days until 2nd wednesday april 2026");
print $result->format("%a days");  # 356 days

# Unix timestamp variant
my $timestamp = Getdate::Getdate::getdate_timestamp("next friday");

# Verify a date expression
if (Getdate::Getdate::verify_valid_date_expression("tomorrow")) {
    print "Valid!";
}
```

### Perl Running Tests

```bash
cd perl
perl -I lib t/01-basic.t
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
- 2nd wednesday next month 2026 ✅
- 202603062145 ✅

- 3/5/2026 21:45 ✅
- 3/5/2026 9:45p ✅
- 2026-03-05 ✅
- ISO 8601: 2026-03-06T14:30:00Z ✅
- Standard Date (US): 03/06/2026 ✅
- Year-Month-Day: 2026-03-06 ✅

- next thursday at noon ✅
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

## Implemented Additional Formats

- RFC 822: `Fri Mar 6 09:45:35 PM EST 2026` ✅
- Full Date & Time: `Monday, March 06, 2026 10:15 AM` ✅
- Standard Date (International): `06/03/2026` or `06-Mar-2026` ✅
- Time (24-hour): `14:30:00` ✅
- Time (12-hour): `02:30:00 PM` ✅
- Time (short 12-hour): `0230p` ✅
- RFC 3339: `2026-03-06 21:54:30+00:00` ✅
- RFC 1123 / RFC 822: `Fri, 06 Mar 2026 21:54:30 GMT` ✅
- Unix Timestamp: `1741305270` ✅

## Not Yet Implemented

None - all formats implemented!

## Validation

The module includes a `validate()` function that parses and validates date expressions, returning detailed error messages for invalid dates.

### Validation Features

- **Date validation**: Catches invalid dates like February 30, April 31
- **Month validation**: Ensures month is 1-12
- **Day validation**: Checks valid days for each month (handles leap years)
- **Time validation**: Validates hour (0-23), minute (0-59), second (0-59)
- **Year validation**: Ensures year is in range 1900-2100

### Python Validation Usage

```python
from getdate_next import validate, ValidationResult

# Validate a date expression
result = validate("2026-02-30")

# Check if valid
if result.valid:
    print("Valid date!")
else:
    print("Invalid date!")
    for error in result.errors:
        print(f"  {error.field}: {error.message}")

# Access error messages easily
print(result.error_messages)  # ['February 30 does not exist (maximum 28 days in February 2026)']
```

### Validation Results

The `validate()` function returns a `ValidationResult` object with:
- `valid`: Boolean indicating if the date is valid
- `errors`: List of `ValidationError` objects with field, value, and message
- `error_messages`: Helper property that returns just the error messages
- `warnings`: List of warnings (e.g., ambiguous dates, timedelta results)

### Validation Examples

```python
validate("2026-02-28")     # Valid ✓
validate("2026-02-29")     # Invalid - not a leap year
validate("2028-02-29")     # Valid ✓ (leap year)
validate("2026-04-31")     # Invalid - April has 30 days
validate("2026-13-01")     # Invalid - month must be 1-12
validate("2026-01-32")     # Invalid - day must be 1-31
validate("2026-03-15T25:00:00")  # Invalid - hour must be 0-23
validate("2026-03-15T12:60:00")  # Invalid - minute must be 0-59
validate("13/01/2026")     # Invalid - month 13 doesn't exist
validate("02/30/2026")     # Invalid - February 30 doesn't exist
validate("1899-01-01")     # Invalid - year too early (min 1900)
validate("2101-01-01")     # Invalid - year too far (max 2100)
```

## Architecture

### Python
```
getdate.py       - Main entry point (getdate(), verify_valid_date_expression())
_parser.py       - Parser functions (extensible)
```

### Perl
```
perl/lib/Getdate/
  Getdate.pm      - Main entry point (getdate(), verify_valid_date_expression())
  Lexer.pm        - Tokenizer
  Parser.pm       - Parser functions (extensible)
  DateTime.pm     - Minimal DateTime-like class (core modules only)
  DateInterval.pm - DateInterval class
```

Each format has its own parser function that can be added to the `parsers` list
in `getdate()`. This makes the system easily extensible for new formats.

## Usage

### Python

```python
from getdate import getdate, verify_valid_date_expression

# Parse a date expression
result = getdate("next friday")
print(result)  # 2026-03-13 20:51:15.080946-05:00

# Validate a date expression
if verify_valid_date_expression("tomorrow"):
    print("Valid!")
```

### Perl

```perl
use Getdate::Getdate;

# Parse a date expression
my $result = Getdate::Getdate::getdate("next friday");
print $result->format("%Y-%m-%d %H:%M:%S");  # 2026-04-23 22:05:00

# Validate a date expression
if (Getdate::Getdate::verify_valid_date_expression("tomorrow")) {
    print "Valid!\n";
}
```

## Running Tests

### Python

```bash
python getdate.py                    # Run all test cases
python getdate.py "next week"        # Test specific expression
```

### Perl

```bash
cd perl
perl -I lib t/01-basic.t
```
