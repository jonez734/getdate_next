# getdate-next

Natural language date expression parser for Python. Parses human-readable date expressions into timezone-aware `datetime` objects or `timedelta` objects.

## Status

**IMPLEMENTED** - Core functionality complete.

## Installation

```bash
pip install getdate-next
```

## Usage

```python
from getdate_next import getdate, verify_valid_date_expression
from datetime import timedelta

# Parse a date expression - returns datetime
result = getdate("next friday")
print(result)  # 2026-04-10 14:00:00-04:00

# Returns timedelta for "days until/since" expressions
result = getdate("days until 2nd wednesday april 2026")
print(result)  # 4 days, 23:59:59.096780
print(type(result))  # <class 'datetime.timedelta'>

# Validate a date expression
if verify_valid_date_expression("tomorrow"):
    print("Valid!")
```

## Supported Formats

### Relative Expressions
- Basic: `now`, `today`, `yesterday`, `tomorrow`
- Units: `next week`, `last week`, `next month`, `next year`
- Days: `next thursday`, `last friday` (and other day names)
- Ordinal: `1st monday of march`, `2nd wednesday of march 2026`
- Final: `final friday of march 2026`
- Duration: `days until 2nd wednesday april 2026` (returns `timedelta`)
- Duration: `days since 2nd wednesday march 2026` (returns `timedelta`)

### Offset Expressions
- `+2 days`, `-3 days`
- `3 days ago`, `72 hours from now`, `48 hours ago`
- `+2 weeks`

### Numeric Formats
- ISO 8601: `2026-03-06`, `2026-03-06T14:30:00Z`
- US Date: `3/5/2026 21:45`, `3/5/2026 9:45p`, `03/06/2026`
- Compact: `202603062145` (YYYYMMDDHHMM)

## Return Types

- **Most expressions** return a timezone-aware `datetime.datetime` object
- **Days until/since expressions** return a `datetime.timedelta` object representing the duration

```python
from datetime import timedelta

result = getdate("days until next friday")
if isinstance(result, timedelta):
    print(f"Days remaining: {result.days}")
```

## Running Tests

```bash
# From source directory
python -m pytest tests/

# Or run the getdate module directly
python src/getdate_next/getdate.py
python src/getdate_next/getdate.py "next week"
```

## Demo Scripts

### demo_moneyday.py

A demo for finding ordinal weekdays (e.g., 2nd Tuesday) across months and identifying which one is today/tomorrow/yesterday or upcoming.

```bash
python -m demo_moneyday
# Or run directly
python demo_moneyday.py
```

The demo prompts for:
- Year
- Month (1-12)
- Day (0=Sun, 1=Mon, etc.)
- Which occurrence (1-4)
- Delta (months to scan)

Example output:
```
2026-01-14 28 days till next
2026-02-11 28 days till next
2026-03-11 28 days till next
2026-04-08 3 days left of 28, 35 (5 weeks) days till next!
2026-05-13 in 38 days
```

Shows days remaining until the next occurrence and indicates when the gap between months is 35 days (5 weeks).

## Development

```bash
# Install in development mode
pip install -e .

# Install with dev dependencies
pip install -e ".[dev]"

# Build package
make build

# Run linter
ruff check src/
ruff format src/
```

## Requirements

- Python 3.9 - 3.12

## License

GPL-2.0-or-later
