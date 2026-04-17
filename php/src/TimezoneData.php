<?php

declare(strict_types=1);

namespace GetdateNext;

use DateInterval;
use DateTimeImmutable;
use DateTimeZone;

class TimezoneData
{
    public const DEBUG = false;

    public const TIMEZONE_OFFSET = [
        'est' => -5,
        'cst' => -6,
        'mst' => -7,
        'pst' => -8,
        'edt' => -4,
        'cdt' => -5,
        'mdt' => -6,
        'pdt' => -7,
        'gmt' => 0,
        'utc' => 0,
        'z' => 0,
        'bst' => 1,
        'cet' => 1,
        'cest' => 2,
        'jst' => 9,
        'aest' => 10,
        'aedt' => 11,
        'nzst' => 12,
        'nzdt' => 13,
    ];

    public const ABBREV_TO_ZONE = [
        'est' => 'America/New_York',
        'cst' => 'America/Chicago',
        'mst' => 'America/Denver',
        'pst' => 'America/Los_Angeles',
        'edt' => 'America/New_York',
        'cdt' => 'America/Chicago',
        'mdt' => 'America/Denver',
        'pdt' => 'America/Los_Angeles',
        'gmt' => 'UTC',
        'bst' => 'Europe/London',
        'cet' => 'Europe/Paris',
        'cest' => 'Europe/Paris',
        'jst' => 'Asia/Tokyo',
        'aest' => 'Australia/Sydney',
        'aedt' => 'Australia/Sydney',
        'nzst' => 'Pacific/Auckland',
        'nzdt' => 'Pacific/Auckland',
    ];

    private static function debug(string $message, mixed ...$args): void
    {
        if (self::DEBUG) {
            fprintf(STDOUT, "[DEBUG] %s\n", sprintf($message, ...$args));
        }
    }

    public static function getTimezone(string $abbrev): ?DateTimeZone
    {
        $abbrev = strtolower($abbrev);
        if (in_array($abbrev, ['utc', 'z'], true)) {
            return new DateTimeZone('UTC');
        }
        if (preg_match('/^([+-])(\d{2}):?(\d{2})$/', $abbrev, $matches)) {
            $sign = $matches[1] === '+' ? '+' : '-';
            $hours = (int)$matches[2];
            $minutes = (int)$matches[3];
            return new DateTimeZone(sprintf('%s%02d:%02d', $sign, $hours, $minutes));
        }

        $zoneName = self::ABBREV_TO_ZONE[$abbrev] ?? null;
        if ($zoneName !== null) {
            try {
                return new DateTimeZone($zoneName);
            } catch (\Exception $e) {
                self::debug("Zone lookup failed for '%s', trying fallback", $abbrev);
            }
        }

        $offset = self::TIMEZONE_OFFSET[$abbrev] ?? null;
        if ($offset === null) {
            return null;
        }

        self::debug("Using fallback offset for '%s': %d", $abbrev, $offset);
        $sign = $offset >= 0 ? '+' : '-';
        $absOffset = abs($offset);
        $hours = intdiv($absOffset, 1);
        $minutes = ($absOffset % 1) * 60;
        return new DateTimeZone(sprintf('%s%02d:%02d', $sign, $hours, $minutes));
    }
}