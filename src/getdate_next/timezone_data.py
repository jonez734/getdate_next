"""
timezone_data.py - Timezone mappings and utilities.

Uses Python's zoneinfo for system timezone data when available,
with fallback to hardcoded offsets.
"""

import logging
from datetime import timezone, timedelta
from typing import Dict, Optional

logger = logging.getLogger(__name__)

try:
    import zoneinfo
    HAS_ZONEINFO = True
except ImportError:
    HAS_ZONEINFO = False
    logger.debug("zoneinfo module not available, using fallback offsets")

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

ABBREV_TO_ZONE: Dict[str, str] = {
    "est": "America/New_York",
    "cst": "America/Chicago",
    "mst": "America/Denver",
    "pst": "America/Los_Angeles",
    "edt": "America/New_York",
    "cdt": "America/Chicago",
    "mdt": "America/Denver",
    "pdt": "America/Los_Angeles",
    "gmt": "UTC",
    "bst": "Europe/London",
    "cet": "Europe/Paris",
    "cest": "Europe/Paris",
    "jst": "Asia/Tokyo",
    "aest": "Australia/Sydney",
    "aedt": "Australia/Sydney",
    "nzst": "Pacific/Auckland",
    "nzdt": "Pacific/Auckland",
}


def get_timezone(abbrev: str) -> Optional[timezone]:
    """Get timezone from abbreviation using system timezone tables."""
    abbrev = abbrev.lower()
    if abbrev in ("utc", "z"):
        return timezone.utc

    if HAS_ZONEINFO:
        zone_name = ABBREV_TO_ZONE.get(abbrev)
        if zone_name:
            try:
                return zoneinfo.ZoneInfo(zone_name)
            except KeyError:
                logger.debug(f"Zoneinfo lookup failed for '%s', trying fallback", abbrev)

    offset = TIMEZONE_ABBREV_OFFSET.get(abbrev)
    if offset is not None:
        logger.debug("Using fallback offset for '%s': %d", abbrev, offset)
        return timezone(timedelta(hours=offset))

    return None
