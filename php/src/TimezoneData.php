<?php

declare(strict_types=1);

namespace GetdateNext;

use DateInterval;
use DateTimeImmutable;
use DateTimeZone;

class TimezoneData
{
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
        $offset = self::TIMEZONE_OFFSET[$abbrev] ?? null;
        if ($offset === null) {
            return null;
        }
        $sign = $offset >= 0 ? '+' : '-';
        $absOffset = abs($offset);
        $hours = intdiv($absOffset, 1);
        $minutes = ($absOffset % 1) * 60;
        return new DateTimeZone(sprintf('%s%02d:%02d', $sign, $hours, $minutes));
    }
}