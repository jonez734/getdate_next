<?php

declare(strict_types=1);

namespace GetdateNext;

use DateInterval;
use DateTimeImmutable;
use DateTimeZone;

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

        if (str_starts_with($bufLower, 'days until ') || str_starts_with($bufLower, 'day until ')) {
            $dateExpr = substr($bufLower, strpos($bufLower, ' ') + 1);
            if (str_starts_with($dateExpr, 'until ')) {
                $dateExpr = substr($dateExpr, 6);
            }
            $target = self::getdate($dateExpr);
            if ($target !== null) {
                $now = new DateTimeImmutable('now', self::getLocalTz());
                return $now->diff($target);
            }
            return null;
        }

        if (str_starts_with($bufLower, 'days since ') || str_starts_with($bufLower, 'day since ')) {
            $dateExpr = substr($bufLower, strpos($bufLower, ' ') + 1);
            if (str_starts_with($dateExpr, 'since ')) {
                $dateExpr = substr($dateExpr, 6);
            }
            $target = self::getdate($dateExpr);
            if ($target !== null) {
                $now = new DateTimeImmutable('now', self::getLocalTz());
                return $target->diff($now);
            }
            return null;
        }

        return Parser::getdateWithLexer($bufLower);
    }

    public static function getdateTimestamp(?string $buf)
    {
        $result = self::getdate($buf);
        if ($result instanceof DateTimeImmutable) {
            return $result->getTimestamp();
        }
        return false;
    }

    public static function verifyValidDateExpression(string $buf): bool
    {
        return self::getdate($buf) !== null;
    }
}