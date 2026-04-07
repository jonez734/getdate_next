# getdate-next PHP

Natural language date expression parser for PHP. Parses human-readable date expressions into timezone-aware `DateTimeImmutable` objects or `DateInterval` objects.

## Status

**IMPLEMENTED** - Core functionality complete.

## Installation

```bash
composer require getdate-next/php
```

## Usage

```php
use GetdateNext\Getdate;

// Parse a date expression - returns DateTimeImmutable
$result = Getdate::getdate("next friday");
echo $result->format('Y-m-d H:i:s');  // 2026-04-10 14:00:00

// Returns DateInterval for "days until/since" expressions
$result = Getdate::getdate("days until 2nd wednesday april 2026");
echo $result->format('%a days');  // 4 days

// Verify a date expression
if (Getdate::verifyValidDateExpression("tomorrow")) {
    echo "Valid!";
}

// Get Unix timestamp instead
$timestamp = Getdate::getdateTimestamp("next friday");
```

## Supported Formats

### Relative Expressions
- Basic: `now`, `today`, `yesterday`, `tomorrow`
- Units: `next week`, `last week`, `next month`, `next year`
- Days: `next thursday`, `last friday` (and other day names)
- Ordinal: `1st monday of march`, `2nd wednesday of march 2026`
- Final: `final friday of march 2026`
- Duration: `days until 2nd wednesday april 2026` (returns `DateInterval`)
- Duration: `days since 2nd wednesday march 2026` (returns `DateInterval`)

### Offset Expressions
- `+2 days`, `-3 days`
- `3 days ago`, `72 hours from now`, `48 hours ago`
- `+2 weeks`

### Numeric Formats
- ISO 8601: `2026-03-06`, `2026-03-06T14:30:00Z`
- US Date: `3/5/2026 21:45`, `3/5/2026 9:45p`, `03/06/2026`
- Compact: `202603062145` (YYYYMMDDHHMM)

## Return Types

- **Most expressions** return a timezone-aware `DateTimeImmutable` object
- **Days until/since expressions** return a `DateInterval` object representing the duration
- **getdateTimestamp()** returns a Unix timestamp (int)

## Running Tests

```bash
composer install
./vendor/bin/phpunit tests/
```

## Requirements

- PHP 7.4+

## License

GPL-2.0-or-later
