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
