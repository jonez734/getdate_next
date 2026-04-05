#!/usr/bin/env python3
"""
Demo: Moneyday using getdate_next

Finds ordinal weekdays (e.g., 2nd Tuesday) across a range of months
and identifies which one is today/tomorrow/yesterday or upcoming.
"""

import datetime
import sys
from typing import Optional

from bbsengine6 import io
from getdate_next import getdate
from getdate_next.getdate import ORDINALS, DAYS


def ordinal_weekday(
    which: int, day_name: str, month: int, year: int
) -> Optional[datetime.date]:
    """Find the Nth weekday of a month (e.g., 2nd Tuesday of March)."""
    day = DAYS.get(day_name.lower())
    if day is None:
        return None

    ordinal = ORDINALS.get(str(which), which)
    if ordinal is None:
        return None

    if month < 1 or month > 12:
        return None

    count = 0
    for d in range(1, 32):
        try:
            dt = datetime.date(year, month, d)
        except ValueError:
            break
        if dt.weekday() == day:
            count += 1
            if count == ordinal:
                return dt
    return None


def adjust_month(month: int, year: int) -> tuple[int, int]:
    """Adjust month, handling year rollover."""
    if month > 12:
        return (month - 12, year + 1)
    elif month < 1:
        return (month + 12, year - 1)
    return (month, year)


def main() -> int:
    today = datetime.datetime.today().date()
    yesterday = today - datetime.timedelta(days=1)
    tomorrow = today + datetime.timedelta(days=1)

    default_year = today.year
    default_month = today.month

    year_input = io.inputinteger(
        f"{{promptcolor}}year {{valuecolor}}[{default_year}]{{promptcolor}}:{{inputcolor}} "
    )
    if year_input is not None:
        year_input.strip()
    year = int(year_input) if year_input is not None else default_year

    month_input = input(f"month (1-12) [{default_month}]: ").strip()
    month = int(month_input) if month_input else default_month

    day_input = input("day (0=sun) [3]: ").strip()
    day = int(day_input) if day_input else 3
    day_names = ("sun", "mon", "tue", "wed", "thu", "fri", "sat")
    day_name = day_names[day]

    which_input = input(f"which {day_name} (1-4) [2]: ").strip()
    which = int(which_input) if which_input else 2

    delta_input = input("delta (months) [3]: ").strip()
    delta = int(delta_input) if delta_input else 3

    io.echo()

    dates: list[datetime.date] = []
    moneyday: Optional[datetime.date] = None

    for d in range(-3, delta + 2):
        m, y = adjust_month(month + d, year)
        target = ordinal_weekday(which, day_name, m, y)
        if target:
            dates.append(target)
            if d == 0:
                moneyday = target

    if not moneyday and dates:
        moneyday = dates[0]

    if moneyday:
        if tomorrow == moneyday:
            io.echo("tomorrow!")
        elif yesterday == moneyday:
            io.echo("yesterday!")
        elif today == moneyday:
            io.echo("today!")

    daystillnext = 0
    if moneyday:
        daystillnext = (moneyday - today).days

    for i, dt in enumerate(dates):
        if i < len(dates) - 1:
            diff = (dates[i + 1] - dt).days
            color = "{yellow}" if diff > 28 else "{green}"
        else:
            diff = 0
            color = "{green}"

        if diff == 35:
            suffix = " (5 weeks)"
        else:
            suffix = ""

        if dt == moneyday:
            if dt < today:
                days_ago = (today - dt).days
                io.echo(f"{{red}} {dt} {days_ago} days ago!")
            elif dt == today:
                io.echo(f"{color} {dt} {diff}{suffix} days till next TODAY!")
            elif dt == tomorrow:
                io.echo(f"{color} {dt} {diff}{suffix} days till next TOMORROW!")
            elif dt == yesterday:
                io.echo(f"{color} {dt} {diff}{suffix} days till next YESTERDAY!")
            elif 0 < daystillnext < 7:
                prev_diff = (dt - dates[i - 1]).days if i > 0 else diff
                weeks_suffix = " (5 weeks)" if diff == 35 else ""
                io.echo(
                    f"{color} {dt} {daystillnext} days left of {prev_diff}, {diff}{weeks_suffix} days till next!"
                )
            else:
                io.echo(f"{color} {dt} {diff}{suffix} days till next")
        elif dt > moneyday:
            days_until = (dt - today).days
            io.echo(f"{color} {dt} in {days_until} days")
        else:
            io.echo(f"{color} {dt} {diff}{suffix} days till next")

    return 0


def demo_getdate_usage() -> None:
    """Demonstrate getdate_next parsing ordinal weekdays."""
    io.echo("=== getdate_next ordinal weekday parsing ===\n")

    expressions = [
        "2nd tuesday of march 2026",
        "3rd friday of april",
        "1st monday of january 2026",
        "4th thursday of november 2026",
        "final friday of december 2026",
    ]

    for expr in expressions:
        result = getdate(expr)
        if result:
            io.echo(f"  {expr!r:45} -> {result.date()}")
        else:
            io.echo(f"  {expr!r:45} -> FAILED")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--demo":
        demo_getdate_usage()
    else:
        sys.exit(main())
