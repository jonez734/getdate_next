<?php

declare(strict_types=1);

namespace GetdateNext;

use DateInterval;
use DateTime;
use DateTimeImmutable;
use DateTimeZone;
use InvalidArgumentException;

class Getdate
{
    private static ?DateTimeZone $localTz = null;

    private static function getLocalTz(): DateTimeZone
    {
        if (self::$localTz === null) {
            self::$localTz = new DateTimeZone(date_default_timezone_get() ?: 'UTC');
        }
        return self::$localTz;
    }

    private static function getNow(): DateTimeImmutable
    {
        return new DateTimeImmutable('now', self::getLocalTz());
    }

    public static function getdate(?string $buf)
    {
        if ($buf === null || $buf === '') {
            return null;
        }

        $buf = trim($buf);
        if ($buf === '') {
            return null;
        }

        $bufLower = strtolower($buf);

        $result = self::parseRelativeWithTime($bufLower);
        if ($result !== null) {
            return $result;
        }

        $result = self::parseAbsoluteNumeric($bufLower);
        if ($result !== null) {
            return $result;
        }

        $result = self::parseIso8601($bufLower);
        if ($result !== null) {
            return $result;
        }

        $result = self::parseUsDatetime($bufLower);
        if ($result !== null) {
            return $result;
        }

        $result = self::parseRelativeOffset($bufLower);
        if ($result !== null) {
            return $result;
        }

        $result = self::parseRelativeDay($bufLower);
        if ($result !== null) {
            return $result;
        }

        $result = self::parseOrdinalDay($bufLower);
        if ($result !== null) {
            return $result;
        }

        $result = self::parseRelativeUnit($bufLower);
        if ($result !== null) {
            return $result;
        }

        $result = self::parseDaysUntil($bufLower);
        if ($result !== null) {
            return $result;
        }

        $result = self::parseDaysSince($bufLower);
        if ($result !== null) {
            return $result;
        }

        return null;
    }

    public static function getdateTimestamp(?string $buf)
    {
        $result = self::getdate($buf);
        if ($result instanceof DateTimeImmutable) {
            return $result->getTimestamp();
        }
        if ($result instanceof DateTime) {
            return $result->getTimestamp();
        }
        return false;
    }

    public static function verifyValidDateExpression(string $buf): bool
    {
        return self::getdate($buf) !== null;
    }

    private static function parseAbsoluteNumeric(string $buf): ?DateTimeImmutable
    {
        if (preg_match('/^(\d{4})(\d{2})(\d{2})(\d{2})(\d{2})$/', $buf, $matches)) {
            if (count($matches) < 6) {
                return null;
            }
            $year = $matches[1];
            $month = $matches[2];
            $day = $matches[3];
            $hour = $matches[4];
            $minute = $matches[5];
            try {
                return new DateTimeImmutable(
                    sprintf('%s-%s-%s %s:%s:00', $year, $month, $day, $hour, $minute),
                    self::getLocalTz()
                );
            } catch (\Exception $e) {
                throw new DateParseError('Invalid date values');
            }
        }
        return null;
    }

    private static function parseIso8601(string $buf): ?DateTimeImmutable
    {
        if (preg_match(
            '/^(\d{4})-(\d{2})-(\d{2})[T ](\d{2}):(\d{2}):(\d{2})(?:\.(\d+))?(Z|[+-]\d{2}:?\d{2})?$/i',
            $buf,
            $matches
        )) {
            $matchesCount = count($matches);
            if ($matchesCount < 6) {
                return null;
            }

            $year = $matches[1];
            $month = $matches[2];
            $day = $matches[3];
            $hour = $matches[4];
            $minute = $matches[5];
            $second = $matches[6];
            $tz = $matches[8] ?? null;
            $tzObj = self::getLocalTz();

            if ($tz !== null) {
                if (strtoupper($tz) === 'Z') {
                    $tzObj = new DateTimeZone('UTC');
                } else {
                    $sign = $tz[0] === '+' ? 1 : -1;
                    $tzParts = substr($tz, 1);
                    if (strpos($tzParts, ':') !== false) {
                        $tzParts = str_replace(':', '', $tzParts);
                    }
                    $tzHours = (int)substr($tzParts, 0, 2);
                    $tzMinutes = (int)substr($tzParts, 2, 2);
                    $totalOffsetMinutes = $sign * ($tzHours * 60 + $tzMinutes);
                    $tzSign = $totalOffsetMinutes >= 0 ? '+' : '-';
                    $tzAbsMinutes = abs($totalOffsetMinutes);
                    $tzObj = new DateTimeZone(sprintf('%s%02d:%02d', $tzSign, (int)($tzAbsMinutes / 60), $tzAbsMinutes % 60));
                }
            }

            try {
                return new DateTimeImmutable(
                    sprintf('%s-%s-%s %s:%s:%s', $year, $month, $day, $hour, $minute, $second),
                    $tzObj
                );
            } catch (\Exception $e) {
                throw new DateParseError('Invalid ISO date');
            }
        }

        if (preg_match('/^(\d{4})-(\d{2})-(\d{2})$/', $buf, $matches)) {
            [, $year, $month, $day] = $matches;
            try {
                return new DateTimeImmutable(
                    sprintf('%s-%s-%s', $year, $month, $day),
                    self::getLocalTz()
                );
            } catch (\Exception $e) {
                throw new DateParseError('Invalid date');
            }
        }

        return null;
    }

    private static function parseUsDatetime(string $buf): ?DateTimeImmutable
    {
        if (preg_match(
            '/^(\d{1,2})\/(\d{1,2})\/(\d{2,4})(?:\s+(\d{1,2}):(\d{2})(?::(\d{2}))?\s*(a|p|am|pm)?)?$/i',
            $buf,
            $matches
        )) {
            $matchesCount = count($matches);
            if ($matchesCount < 4) {
                return null;
            }

            $month = (int)$matches[1];
            $day = (int)$matches[2];
            $yearStr = $matches[3];
            $hour = $matches[4] ?? null;
            $minute = $matches[5] ?? null;
            $second = $matches[6] ?? null;
            $ampm = $matches[7] ?? null;

            if (strlen($yearStr) === 2) {
                $year = (int)$yearStr + 2000;
                if ($year < 1970) {
                    $year += 100;
                }
            } else {
                $year = (int)$yearStr;
            }

            if ($hour === null) {
                $hour = 0;
                $minute = 0;
                $second = 0;
            } else {
                $hour = (int)$hour;
                $minute = (int)$minute;
                $second = $second !== null ? (int)$second : 0;

                if ($ampm !== null) {
                    $ampm = strtolower($ampm);
                    if ($ampm === 'p' || $ampm === 'pm') {
                        if ($hour !== 12) {
                            $hour += 12;
                        }
                    } elseif ($ampm === 'a' || $ampm === 'am') {
                        if ($hour === 12) {
                            $hour = 0;
                        }
                    }
                }
            }

            try {
                return new DateTimeImmutable(
                    sprintf('%d-%02d-%02d %02d:%02d:%02d', $year, $month, $day, $hour, $minute, $second),
                    self::getLocalTz()
                );
            } catch (\Exception $e) {
                throw new DateParseError('Invalid US date');
            }
        }

        return null;
    }

    private static function parseTime(string $timeStr): ?array
    {
        $timeStr = strtolower(trim($timeStr));

        $specialTimes = [
            'noon' => [12, 0],
            'midday' => [12, 0],
            'midnight' => [0, 0],
            'night' => [21, 0],
        ];
        if (isset($specialTimes[$timeStr])) {
            return $specialTimes[$timeStr];
        }

        if (preg_match('/^(\d{1,2}):(\d{2})(?::(\d{2}))?\s*(a|p|am|pm)?$/i', $timeStr, $matches)) {
            [, $hour, $minute, $second, $ampm] = $matches;
            $hour = (int)$hour;
            $minute = (int)$minute;

            if ($ampm !== null) {
                $ampm = strtolower($ampm);
                if ($ampm === 'p' || $ampm === 'pm') {
                    if ($hour !== 12) {
                        $hour += 12;
                    }
                } elseif ($ampm === 'a' || $ampm === 'am') {
                    if ($hour === 12) {
                        $hour = 0;
                    }
                }
            }

            if ($hour >= 0 && $hour <= 23 && $minute >= 0 && $minute <= 59) {
                return [$hour, $minute];
            }
        }

        if (preg_match('/^(\d{1,2})\s*(a|p|am|pm)?$/i', $timeStr, $matches)) {
            $hour = (int)$matches[1];
            $ampm = $matches[2] ?? null;

            if ($ampm !== null) {
                $ampm = strtolower($ampm);
                if ($ampm === 'p' || $ampm === 'pm') {
                    if ($hour !== 12) {
                        $hour += 12;
                    }
                } elseif ($ampm === 'a' || $ampm === 'am') {
                    if ($hour === 12) {
                        $hour = 0;
                    }
                }
            }

            if ($hour >= 0 && $hour <= 23) {
                return [$hour, 0];
            }
        }

        return null;
    }

    private static function parseRelativeWithTime(string $buf): ?DateTimeImmutable
    {
        $now = self::getNow();

        $simpleRelative = [
            'today' => 0,
            'yesterday' => -1,
            'tomorrow' => 1,
        ];

        foreach ($simpleRelative as $relDay => $dayOffset) {
            $prefix = $relDay . ' ';
            if (strpos($buf, $prefix) === 0) {
                $timeStr = substr($buf, strlen($prefix));
                $timeParsed = self::parseTime($timeStr);
                if ($timeParsed !== null) {
                    [$hour, $minute] = $timeParsed;
                    $targetDate = clone $now;
                    $targetDate = $targetDate->modify(($dayOffset >= 0 ? '+' : '') . $dayOffset . ' days');
                    return new DateTimeImmutable(
                        sprintf('%d-%02d-%02d %02d:%02d:00', $targetDate->format('Y'), $targetDate->format('m'), $targetDate->format('d'), $hour, $minute),
                        self::getLocalTz()
                    );
                }
            }
        }

        if (preg_match(
            '/^(next|last|previous)\s+(monday|tuesday|wednesday|thursday|friday|saturday|sunday|mon|tue|wed|thu|fri|sat|sun)\s+(\d{1,2}(?::\d{2})?(?:\s*[ap]\.?m\.?)?)$/i',
            $buf,
            $matches
        )) {
            [, $direction, $dayName, $timeStr] = $matches;
            $targetDay = DayInfo::DAYS[strtolower($dayName)];
            $timeParsed = self::parseTime($timeStr);

            if ($timeParsed === null) {
                return null;
            }

            [$hour, $minute] = $timeParsed;
            $daysAhead = $targetDay - (int)$now->format('N') + 1;
            if ($daysAhead <= 0) {
                $daysAhead += 7;
            }

            if (strtolower($direction) === 'last' || strtolower($direction) === 'previous') {
                $daysAhead -= 14;
            }

            $targetDate = $now->modify(sprintf('%+d days', $daysAhead));
            return new DateTimeImmutable(
                sprintf('%d-%02d-%02d %02d:%02d:00', $targetDate->format('Y'), $targetDate->format('m'), $targetDate->format('d'), $hour, $minute),
                self::getLocalTz()
            );
        }

        if (preg_match('/^(monday|tuesday|wednesday|thursday|friday|saturday|sunday|mon|tue|wed|thu|fri|sat|sun)\s+(\d{1,2}(?::\d{2})?(?:\s*[ap]\.?m\.?)?)$/i', $buf, $matches)) {
            [, $dayName, $timeStr] = $matches;
            $targetDay = DayInfo::DAYS[strtolower($dayName)];
            $timeParsed = self::parseTime($timeStr);

            if ($timeParsed !== null) {
                [$hour, $minute] = $timeParsed;
                $daysAhead = $targetDay - (int)$now->format('N') + 1;
                if ($daysAhead <= 0) {
                    $daysAhead += 7;
                }

                $targetDate = $now->modify(sprintf('%+d days', $daysAhead));
                return new DateTimeImmutable(
                    sprintf('%d-%02d-%02d %02d:%02d:00', $targetDate->format('Y'), $targetDate->format('m'), $targetDate->format('d'), $hour, $minute),
                    self::getLocalTz()
                );
            }
        }

        return null;
    }

    private static function parseRelativeOffset(string $buf): ?DateTimeImmutable
    {
        if (preg_match(
            '/^([+-]?)(\d+)\s+(days?|weeks?|months?|hours?|minutes?|seconds?)\s*(ago|from now)?$/',
            $buf,
            $matches
        )) {
            $matchesCount = count($matches);
            if ($matchesCount < 3) {
                return null;
            }

            $signStr = $matches[1] ?? '';
            $amount = (int)$matches[2];
            $unit = $matches[3] ?? '';
            $direction = $matches[4] ?? '';

            $sign = ($signStr === '-' || $direction === 'ago') ? -1 : 1;
            $amount *= $sign;

            $now = self::getNow();

            if (in_array($unit, ['day', 'days'], true)) {
                return $now->modify(sprintf('%+d days', $amount));
            }
            if (in_array($unit, ['week', 'weeks'], true)) {
                return $now->modify(sprintf('%+d weeks', $amount));
            }
            if (in_array($unit, ['hour', 'hours'], true)) {
                return $now->modify(sprintf('%+d hours', $amount));
            }
            if (in_array($unit, ['minute', 'minutes'], true)) {
                return $now->modify(sprintf('%+d minutes', $amount));
            }
            if (in_array($unit, ['second', 'seconds'], true)) {
                return $now->modify(sprintf('%+d seconds', $amount));
            }
            if (in_array($unit, ['month', 'months'], true)) {
                return self::addMonths($now, $amount);
            }
        }

        return null;
    }

    private static function addMonths(DateTimeImmutable $date, int $months): DateTimeImmutable
    {
        $year = (int)$date->format('Y');
        $month = (int)$date->format('m') + $months;
        $day = (int)$date->format('d');

        while ($month > 12) {
            $month -= 12;
            $year++;
        }
        while ($month < 1) {
            $month += 12;
            $year--;
        }

        $maxDay = (int)date('t', mktime(0, 0, 0, $month, 1, $year));
        $day = min($day, $maxDay);

        return new DateTimeImmutable(
            sprintf('%d-%02d-%02d %02d:%02d:%02d', $year, $month, $day, $date->format('H'), $date->format('i'), $date->format('s')),
            $date->getTimezone()
        );
    }

    private static function parseRelativeDay(string $buf): ?DateTimeImmutable
    {
        if (preg_match(
            '/^(next|last|previous)\s+(monday|tuesday|wednesday|thursday|friday|saturday|sunday|mon|tue|wed|thu|fri|sat|sun)$/i',
            $buf,
            $matches
        )) {
            [, $direction, $dayName] = $matches;
            $now = self::getNow();
            $targetDay = DayInfo::DAYS[strtolower($dayName)];
            $phpWeekday = (int)$now->format('N');

            $daysAhead = $targetDay - $phpWeekday + 1;
            if ($daysAhead <= 0) {
                $daysAhead += 7;
            }

            if (strtolower($direction) === 'last' || strtolower($direction) === 'previous') {
                if ($daysAhead >= 0) {
                    $daysAhead -= 7;
                }
            }

            return $now->modify(sprintf('%+d days', $daysAhead));
        }

        if (isset(DayInfo::DAYS[$buf])) {
            $now = self::getNow();
            $targetDay = DayInfo::DAYS[$buf];
            $phpWeekday = (int)$now->format('N');

            $daysAhead = $targetDay - $phpWeekday + 1;
            if ($daysAhead <= 0) {
                $daysAhead += 7;
            }

            return $now->modify(sprintf('%+d days', $daysAhead));
        }

        return null;
    }

    private static function parseOrdinalDay(string $buf): ?DateTimeImmutable
    {
        $now = self::getNow();

        if (preg_match(
            '/^(\d+(?:st|nd|rd|th)?|first|second|third|fourth|fifth)\s+(monday|tuesday|wednesday|thursday|friday|saturday|sunday|mon|tue|wed|thu|fri|sat|sun)\s+(?:of\s+)?(?:(january|february|march|april|may|june|july|august|september|october|november|december|jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\s*)?(\d{4})?$/i',
            $buf,
            $matches
        )) {
            $matchesCount = count($matches);
            if ($matchesCount < 3) {
                return null;
            }

            $ordinalStr = $matches[1];
            $dayName = $matches[2];
            $monthStr = $matches[3] ?? null;
            $yearStr = $matches[4] ?? null;

            if (preg_match('/^\d+/', $ordinalStr, $ordinalMatch)) {
                $ordinal = (int)$ordinalMatch[0];
            } else {
                $ordinal = DayInfo::ORDINALS[strtolower($ordinalStr)] ?? 1;
            }

            $targetDay = DayInfo::DAYS[strtolower($dayName)];

            if ($monthStr !== null) {
                $month = DayInfo::MONTHS[strtolower($monthStr)];
            } else {
                $month = (int)$now->format('m');
            }

            $year = $yearStr !== null ? (int)$yearStr : (int)$now->format('Y');

            $count = 0;
            $maxDay = (int)date('t', mktime(0, 0, 0, $month, 1, $year));
            for ($d = 1; $d <= $maxDay; $d++) {
                $dt = mktime(0, 0, 0, $month, $d, $year);
                if (date('N', $dt) === strval($targetDay + 1)) {
                    $count++;
                    if ($count === $ordinal) {
                        return new DateTimeImmutable(
                            sprintf('%d-%02d-%02d %02d:%02d:%02d', $year, $month, $d, $now->format('H'), $now->format('i'), $now->format('s')),
                            self::getLocalTz()
                        );
                    }
                }
            }

            throw new DateParseError("No {$ordinalStr} {$dayName} in {$month}/{$year}");
        }

        if (preg_match(
            '/^final\s+(monday|tuesday|wednesday|thursday|friday|saturday|sunday|mon|tue|wed|thu|fri|sat|sun)\s+(?:of\s+)?(?:(january|february|march|april|may|june|july|august|september|october|november|december|jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\s*)?(\d{4})?$/i',
            $buf,
            $matches
        )) {
            [, $dayName, $monthStr, $yearStr] = $matches;

            $targetDay = DayInfo::DAYS[strtolower($dayName)];

            if ($monthStr !== null) {
                $month = DayInfo::MONTHS[strtolower($monthStr)];
            } else {
                $month = (int)$now->format('m');
            }

            $year = $yearStr !== null ? (int)$yearStr : (int)$now->format('Y');

            $maxDay = (int)date('t', mktime(0, 0, 0, $month, 1, $year));
            $lastOccurrence = null;
            for ($d = $maxDay; $d >= 1; $d--) {
                $dt = mktime(0, 0, 0, $month, $d, $year);
                if (date('N', $dt) === strval($targetDay + 1)) {
                    $lastOccurrence = $d;
                    break;
                }
            }

            if ($lastOccurrence !== null) {
                return new DateTimeImmutable(
                    sprintf('%d-%02d-%02d %02d:%02d:%02d', $year, $month, $lastOccurrence, $now->format('H'), $now->format('i'), $now->format('s')),
                    self::getLocalTz()
                );
            }

            throw new DateParseError("No {$dayName} in {$month}/{$year}");
        }

        return null;
    }

    private static function parseRelativeUnit(string $buf): ?DateTimeImmutable
    {
        $simpleMapping = [
            'today' => 0,
            'yesterday' => -1,
            'tomorrow' => 1,
            'now' => 0,
        ];

        $now = self::getNow();

        if (isset($simpleMapping[$buf])) {
            return $now->modify(sprintf('%+d days', $simpleMapping[$buf]));
        }

        if (preg_match('/^(next|last|previous)\s+(week|month|year)$/i', $buf, $matches)) {
            [, $direction, $unit] = $matches;

            if (strtolower($unit) === 'week') {
                $days = strtolower($direction) === 'next' ? 7 : -7;
                return $now->modify(sprintf('%+d days', $days));
            }
            if (strtolower($unit) === 'month') {
                $months = strtolower($direction) === 'next' ? 1 : -1;
                return self::addMonths($now, $months);
            }
            if (strtolower($unit) === 'year') {
                $years = strtolower($direction) === 'next' ? 1 : -1;
                return self::addYears($now, $years);
            }
        }

        return null;
    }

    private static function addYears(DateTimeImmutable $date, int $years): DateTimeImmutable
    {
        $year = (int)$date->format('Y') + $years;
        $month = (int)$date->format('m');
        $day = (int)$date->format('d');

        $maxDay = (int)date('t', mktime(0, 0, 0, $month, 1, $year));
        $day = min($day, $maxDay);

        return new DateTimeImmutable(
            sprintf('%d-%02d-%02d %02d:%02d:%02d', $year, $month, $day, $date->format('H'), $date->format('i'), $date->format('s')),
            $date->getTimezone()
        );
    }

    private static function parseDaysUntil(string $buf): ?DateInterval
    {
        if (preg_match('/^days?\s+until\s+(.+)$/i', $buf, $matches)) {
            $dateExpr = trim($matches[1]);

            $targetDate = self::getdate($dateExpr);

            if ($targetDate === null) {
                $targetDate = self::parseOrdinalDay($dateExpr);
            }
            if ($targetDate === null) {
                $targetDate = self::parseRelativeDay($dateExpr);
            }
            if ($targetDate === null) {
                $targetDate = self::parseIso8601($dateExpr);
            }
            if ($targetDate === null) {
                $targetDate = self::parseUsDatetime($dateExpr);
            }
            if ($targetDate === null) {
                $targetDate = self::parseAbsoluteNumeric($dateExpr);
            }

            if ($targetDate !== null) {
                $now = self::getNow();
                if ($targetDate instanceof DateTime) {
                    $targetDate = DateTimeImmutable::createFromFormat('Y-m-d H:i:s', $targetDate->format('Y-m-d H:i:s'), $targetDate->getTimezone());
                }
                $diff = $now->diff($targetDate);
                return $diff;
            }
        }

        return null;
    }

    private static function parseDaysSince(string $buf): ?DateInterval
    {
        if (preg_match('/^days?\s+since\s+(.+)$/i', $buf, $matches)) {
            $dateExpr = trim($matches[1]);

            $targetDate = self::getdate($dateExpr);

            if ($targetDate === null) {
                $targetDate = self::parseOrdinalDay($dateExpr);
            }
            if ($targetDate === null) {
                $targetDate = self::parseRelativeDay($dateExpr);
            }
            if ($targetDate === null) {
                $targetDate = self::parseIso8601($dateExpr);
            }
            if ($targetDate === null) {
                $targetDate = self::parseUsDatetime($dateExpr);
            }
            if ($targetDate === null) {
                $targetDate = self::parseAbsoluteNumeric($dateExpr);
            }

            if ($targetDate !== null) {
                $now = self::getNow();
                if ($targetDate instanceof DateTime) {
                    $targetDate = DateTimeImmutable::createFromFormat('Y-m-d H:i:s', $targetDate->format('Y-m-d H:i:s'), $targetDate->getTimezone());
                }
                $diff = $now->diff($targetDate);
                return $diff;
            }
        }

        return null;
    }
}
