# datetime expression evaluator returns a timezone aware datetime.datetime object

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

## examples of input:

- 2nd wednesday of march 2026
- 2nd wednesday next month 2026
- 202603062145

- Fri Mar  6 09:45:35 PM EST 2026
- 3/5/2026 21:45
- 3/5/2026 9:45p
- 2026-03-05
- ISO 8601 (International Standard): 2026-03-06T14:30:00Z or 2026-03-06T09:30:00-05:00
- Full Date & Time (Detailed): Monday, March 06, 2026 10:15 AM
- Standard Date (US): 03/06/2026
- Standard Date (International): 06/03/2026 or 06-Mar-2026
- Year-Month-Day: 2026-03-06
- Time (24-hour): 14:30:00
- Time (12-hour): 02:30:00 PM 
- Time (short 12-hour): 0230p
- ISO 8601 (Extended): The primary international standard for date and time representation.
    Example: 2026-03-06T21:54:30Z
- RFC 3339: A profile of ISO 8601 often used for internet protocols.
    Example: 2026-03-06 21:54:30+00:00
- RFC 1123 / RFC 822: Standard used in HTTP headers and email.
    Example: Fri, 06 Mar 2026 21:54:30 GMT

- Unix Timestamp: The number of seconds elapsed since January 1, 1970 GMT
    Example: 1741305270

Common Components & Symbols

    YYYY: 4-digit year (2026)
    MM: 2-digit month (01-12)
    MMM: Abbreviated month (Jan, Feb, Mar)
    DD: 2-digit day (01-31)
    HH: 2-digit hour 00-23
    mm: 2-digit minute 00-59
    ss: 2-digit second 00-59
    tt: AM/PM designator 

Common Time Formats
Time is typically represented in either a 12-hour or 24-hour cycle. 

    24-Hour Clock (Military Time): Standard for transport, medicine, and military.
        Example: 21:54:30
    12-Hour Clock: Common for everyday social use.
        Example: 9:54 PM
    High Precision: Includes fractions of a second.
        Example: 21:54:30.123 

Human-Readable & Descriptive Formats
Used in documents, journalism, and software interfaces for better readability. 

    Short: 3/6/26 or 03-06-2026
    Medium: Mar 6, 2026
    Long: March 6, 2026
    Full: Friday, March 6, 2026

- next thursday at noon
- last friday
- final friday of march 2026
- 1st monday of march
- next week
- next month
- 3 days ago
- 3 days from today
- 72 hours from now
- 48 hours ago
- +/-72 hours
- yesterday
- tomorrow
- +2 weeks
