"""
timezone_data.py - Timezone mappings and utilities.

Uses Python's zoneinfo for system timezone data.
"""

from datetime import timezone, timedelta
from typing import Dict, Optional

TIMEZONE_ABBREV_OFFSET: Dict[str, int] = {
    "est": -5,
    "cst": -6,
    "mst": -7,
    "pst": -8,
    "edt": -4,
    "cdt": -5,
    "mdt": -6,
    "pdt": -7,
    "gmt": 0,
    "utc": 0,
    "z": 0,
    "bst": 1,
    "cet": 1,
    "cest": 2,
    "jst": 9,
    "aest": 10,
    "aedt": 11,
    "nzst": 12,
    "nzdt": 13,
}


def get_timezone(abbrev: str) -> Optional[timezone]:
    """Get timezone from abbreviation."""
    abbrev = abbrev.lower()
    if abbrev in ("utc", "z"):
        return timezone.utc
    offset = TIMEZONE_ABBREV_OFFSET.get(abbrev)
    if offset is not None:
        return timezone(timedelta(hours=offset))
    return None
