<?php

declare(strict_types=1);

namespace GetdateNext;

use DateInterval;
use DateTimeImmutable;
use DateTimeZone;
use InvalidArgumentException;

class Parser
{
    private const DAYS = [
        'monday' => 0, 'tuesday' => 1, 'wednesday' => 2, 'thursday' => 3,
        'friday' => 4, 'saturday' => 5, 'sunday' => 6,
        'mon' => 0, 'tue' => 1, 'wed' => 2, 'thu' => 3, 'fri' => 4, 'sat' => 5, 'sun' => 6,
    ];
    private const MONTHS = [
        'january' => 1, 'february' => 2, 'march' => 3, 'april' => 4, 'may' => 5, 'june' => 6,
        'july' => 7, 'august' => 8, 'september' => 9, 'october' => 10, 'november' => 11, 'december' => 12,
        'jan' => 1, 'feb' => 2, 'mar' => 3, 'apr' => 4, 'jun' => 6, 'jul' => 7, 'aug' => 8, 'sep' => 9, 'oct' => 10, 'nov' => 11, 'dec' => 12,
    ];
    private const ORDINALS = [
        'first' => 1, 'second' => 2, 'third' => 3, 'fourth' => 4, 'fifth' => 5, 'sixth' => 6,
        'seventh' => 7, 'eighth' => 8, 'ninth' => 9, 'tenth' => 10, 'eleventh' => 11, 'twelfth' => 12,
        '1st' => 1, '2nd' => 2, '3rd' => 3, '4th' => 4, '5th' => 5, '6th' => 6, '7th' => 7, '8th' => 8, '9th' => 9, '10th' => 10, '11th' => 11, '12th' => 12,
    ];

    private array $tokens;
    private int $pos = 0;
    private DateTimeImmutable $now;
    private DateTimeZone $localTz;

    public function __construct(array $tokens)
    {
        $this->tokens = $tokens;
        $this->now = new DateTimeImmutable('now');
        $this->localTz = $this->now->getTimezone();
    }

    public function parse(): ?DateTimeImmutable
    {
        if (empty($this->tokens) || $this->tokens[0]->type === TokenType::EOF) {
            return null;
        }

        $parsers = [
            [$this, 'parseUnixTimestamp'],
            [$this, 'parseAbsoluteNumeric'],
            [$this, 'parseRfc822'],
            [$this, 'parseRfc1123'],
            [$this, 'parseRfc3339'],
            [$this, 'parseFullDateTime'],
            [$this, 'parseUsDatetime'],
            [$this, 'parseInternationalDate'],
            [$this, 'parseIso8601'],
            [$this, 'parseRelativeWithTime'],
            [$this, 'parseDayAtTime'],
            [$this, 'parseOrdinalWithRelative'],
            [$this, 'parseRelativeOffset'],
            [$this, 'parseRelativeDay'],
            [$this, 'parseOrdinalDay'],
            [$this, 'parseRelativeUnit'],
            [$this, 'parseDaysUntil'],
            [$this, 'parseDaysSince'],
            [$this, 'parse24HourTime'],
            [$this, 'parse12HourTime'],
            [$this, 'parseShort12HourTime'],
        ];

        foreach ($parsers as $parser) {
            $result = $parser();
            if ($result !== null) {
                return $result;
            }
        }

        return null;
    }

    private function peek(): Token
    {
        return $this->tokens[$this->pos] ?? $this->tokens[count($this->tokens) - 1];
    }

    private function advance(): Token
    {
        return $this->tokens[$this->pos++];
    }

    private function reset(): void
    {
        $this->pos = 0;
    }

    private function parseTime(string $timeVal): ?array
    {
        $timeVal = strtolower(trim($timeVal));
        $specialTimes = ['noon' => [12, 0], 'midday' => [12, 0], 'midnight' => [0, 0], 'night' => [21, 0]];
        if (isset($specialTimes[$timeVal])) {
            return $specialTimes[$timeVal];
        }

        if (preg_match('/^(\d{1,2}):(\d{2})(?::(\d{2}))?\s*(a|p|am|pm)?$/i', $timeVal, $matches)) {
            $hour = (int)$matches[1];
            $minute = (int)$matches[2];
            $ampm = $matches[4] ?? null;
            if ($ampm !== null) {
                $ampm = strtolower($ampm);
                if (in_array($ampm, ['p', 'pm'], true) && $hour !== 12) {
                    $hour += 12;
                } elseif (in_array($ampm, ['a', 'am'], true) && $hour === 12) {
                    $hour = 0;
                }
            }
            if ($hour >= 0 && $hour <= 23 && $minute >= 0 && $minute <= 59) {
                return [$hour, $minute];
            }
        }

        if (preg_match('/^(\d{1,2})\s*(a|p|am|pm)?$/i', $timeVal, $matches)) {
            $hour = (int)$matches[1];
            $ampm = $matches[2] ?? null;
            if ($ampm !== null) {
                $ampm = strtolower($ampm);
                if (in_array($ampm, ['p', 'pm'], true) && $hour !== 12) {
                    $hour += 12;
                } elseif (in_array($ampm, ['a', 'am'], true) && $hour === 12) {
                    $hour = 0;
                }
            }
            if ($hour >= 0 && $hour <= 23) {
                return [$hour, 0];
            }
        }

        return null;
    }

    private function parseUnixTimestamp(): ?DateTimeImmutable
    {
        if ($this->peek()->type !== TokenType::UNIX) {
            return null;
        }
        $this->advance();
        $ts = (int)$this->tokens[$this->pos - 1]->value;
        return (new DateTimeImmutable())->setTimestamp($ts)->setTimezone($this->localTz);
    }

    private function parseAbsoluteNumeric(): ?DateTimeImmutable
    {
        if ($this->pos !== 0) {
            return null;
        }
        $buf = $this->tokens[0]?->value ?? '';
        if (strlen($buf) !== 12 || !ctype_digit($buf)) {
            return null;
        }
        $year = (int)substr($buf, 0, 4);
        $month = (int)substr($buf, 4, 2);
        $day = (int)substr($buf, 6, 2);
        $hour = (int)substr($buf, 8, 2);
        $minute = (int)substr($buf, 10, 2);
        try {
            return new DateTimeImmutable(sprintf('%d-%02d-%02d %02d:%02d:00', $year, $month, $day, $hour, $minute), $this->localTz);
        } catch (\Exception $e) {
            throw new DateParseError('Invalid date');
        }
    }

    private function parseRfc822(): ?DateTimeImmutable
    {
        $buf = $this->reconstruct();
        if (preg_match('/^([a-z]{3})\s+([a-z]{3})\s+(\d{1,2})\s+(\d{1,2}):(\d{2}):(\d{2})\s+(am|pm)\s+([a-z]{3})\s+(\d{4})$/i', $buf, $matches)) {
            [, , $monthStr, , $hour, $minute, $second, $ampm, $tzAbbr, $year] = $matches;
            $hour = (int)$hour;
            $minute = (int)$minute;
            $second = (int)$second;
            $ampm = strtolower($ampm);
            if ($ampm === 'pm' && $hour !== 12) {
                $hour += 12;
            } elseif ($ampm === 'am' && $hour === 12) {
                $hour = 0;
            }
            $month = self::MONTHS[strtolower($monthStr)] ?? null;
            if ($month === null) {
                return null;
            }
            $tz = TimezoneData::getTimezone($tzAbbr) ?? new DateTimeZone('UTC');
            return new DateTimeImmutable(sprintf('%d-%02d-%02d %02d:%02d:%02d', (int)$year, $month, (int)$matches[3], $hour, $minute, $second), $tz);
        }
        return null;
    }

    private function parseRfc1123(): ?DateTimeImmutable
    {
        $buf = $this->reconstructComma();
        if (preg_match('/^([a-z]{3}),?\s+(\d{1,2})\s+([a-z]{3})\s+(\d{4})\s+(\d{1,2}):(\d{2}):(\d{2})\s+([a-z]{3,4})$/i', $buf, $matches)) {
            [, , $day, $monthStr, $year, $hour, $minute, $second, $tzAbbr] = $matches;
            $month = self::MONTHS[strtolower($monthStr)] ?? null;
            if ($month === null) {
                return null;
            }
            $tz = TimezoneData::getTimezone($tzAbbr) ?? new DateTimeZone('UTC');
            return new DateTimeImmutable(sprintf('%d-%02d-%02d %02d:%02d:%02d', (int)$year, $month, (int)$day, (int)$hour, (int)$minute, (int)$second), $tz);
        }
        return null;
    }

    private function parseRfc3339(): ?DateTimeImmutable
    {
        $buf = $this->reconstructWithTimezone();
        if (preg_match('/^(\d{4})-(\d{2})-(\d{2})\s+(\d{2}):(\d{2}):(\d{2})([+-]\d{2}:\d{2}|Z)?$/i', $buf, $matches)) {
            $tz = $matches[7] ?? null;
            $tzObj = $this->localTz;
            if ($tz !== null) {
                if (strtoupper($tz) === 'Z') {
                    $tzObj = new DateTimeZone('UTC');
                } else {
                    $tzObj = TimezoneData::getTimezone($tz) ?? $this->localTz;
                }
            }
            return new DateTimeImmutable(sprintf('%d-%02d-%02d %02d:%02d:%02d', (int)$matches[1], (int)$matches[2], (int)$matches[3], (int)$matches[4], (int)$matches[5], (int)$matches[6]), $tzObj);
        }
        return null;
    }

    private function parseFullDateTime(): ?DateTimeImmutable
    {
        $saved = $this->pos;
        if ($this->peek()->type !== TokenType::DAY) {
            return null;
        }
        $this->advance();
        if ($this->peek()->type !== TokenType::COMMA) {
            $this->pos = $saved;
            return null;
        }
        $this->advance();
        if ($this->peek()->type !== TokenType::MONTH) {
            $this->pos = $saved;
            return null;
        }
        $monthTok = $this->advance();
        if ($this->peek()->type !== TokenType::NUMBER) {
            $this->pos = $saved;
            return null;
        }
        $dayTok = $this->advance();
        if ($this->peek()->type !== TokenType::COMMA) {
            $this->pos = $saved;
            return null;
        }
        $this->advance();
        if ($this->peek()->type !== TokenType::NUMBER) {
            $this->pos = $saved;
            return null;
        }
        $yearTok = $this->advance();
        if ($this->peek()->type !== TokenType::TIME) {
            $this->pos = $saved;
            return null;
        }
        $timeTok = $this->advance();
        $ampmTok = $this->peek();
        $ampm = null;
        if ($ampmTok->type === TokenType::TIME && in_array($ampmTok->value, ['am', 'pm', 'a', 'p'], true)) {
            $ampm = strtolower($ampmTok->value);
            $this->advance();
        }
        $timeParsed = self::parseTime($timeTok->value);
        if ($timeParsed === null) {
            $this->pos = $saved;
            return null;
        }
        [$hour, $minute] = $timeParsed;
        if ($ampm !== null) {
            if (in_array($ampm, ['pm', 'p']) && $hour !== 12) {
                $hour += 12;
            } elseif (in_array($ampm, ['am', 'a']) && $hour === 12) {
                $hour = 0;
            }
        }
        return new DateTimeImmutable(sprintf('%d-%02d-%02d %02d:%02d:00', (int)$yearTok->value, self::MONTHS[$monthTok->value], (int)$dayTok->value, $hour, $minute), $this->localTz);
    }

    private function parseInternationalDate(): ?DateTimeImmutable
    {
        $buf = $this->reconstructSep();
        if (preg_match('/^(\d{1,2})\/(\d{1,2})\/(\d{2,4})$/', $buf, $matches)) {
            $first = (int)$matches[1];
            $second = (int)$matches[2];
            if ($first <= 12 && $second <= 12) {
                $day = $first;
                $month = $second;
            } elseif ($first > 12) {
                $day = $first;
                $month = $second;
            } else {
                $day = $second;
                $month = $first;
            }
            $year = strlen($matches[3]) === 2 ? (int)$matches[3] + 2000 : (int)$matches[3];
            return new DateTimeImmutable(sprintf('%d-%02d-%02d', $year, $month, $day), $this->localTz);
        }
        if (preg_match('/^(\d{1,2})-([a-z]{3})-(\d{4})$/i', $buf, $matches)) {
            $month = self::MONTHS[strtolower($matches[2])] ?? null;
            if ($month === null) {
                return null;
            }
            return new DateTimeImmutable(sprintf('%d-%02d-%02d', (int)$matches[3], $month, (int)$matches[1]), $this->localTz);
        }
        return null;
    }

    private function parseUsDatetime(): ?DateTimeImmutable
    {
        $hasSep = false;
        foreach ($this->tokens as $tok) {
            if ($tok->type === TokenType::DATE_SEPARATOR) {
                $hasSep = true;
                break;
            }
        }
        if (!$hasSep) {
            return null;
        }
        $buf = $this->reconstructSep();
        if (preg_match('/^(\d{1,2})\/(\d{1,2})\/(\d{2,4})(?:\s+(\d{1,2}):(\d{2})(?::(\d{2}))?\s*(a|p|am|pm)?)?$/i', $buf, $matches)) {
            $month = (int)$matches[1];
            $day = (int)$matches[2];
            $yearStr = $matches[3];
            $year = strlen($yearStr) === 2 ? (int)$yearStr + 2000 : (int)$yearStr;
            if ($year < 1970 && strlen($yearStr) === 2) {
                $year += 100;
            }
            $hour = isset($matches[4]) ? (int)$matches[4] : 0;
            $minute = isset($matches[5]) ? (int)$matches[5] : 0;
            $second = isset($matches[6]) ? (int)$matches[6] : 0;
            $ampm = $matches[7] ?? null;
            if ($ampm !== null) {
                $ampm = strtolower($ampm);
                if (in_array($ampm, ['p', 'pm'], true) && $hour !== 12) {
                    $hour += 12;
                } elseif (in_array($ampm, ['a', 'am'], true) && $hour === 12) {
                    $hour = 0;
                }
            }
            return new DateTimeImmutable(sprintf('%d-%02d-%02d %02d:%02d:%02d', $year, $month, $day, $hour, $minute, $second), $this->localTz);
        }
        return null;
    }

    private function parseIso8601(): ?DateTimeImmutable
    {
        $buf = $this->reconstructWithTimezone();
        if (preg_match('/^(\d{4})-(\d{2})-(\d{2})[T ](\d{2}):(\d{2}):(\d{2})(?:\.(\d+))?(Z|[+-]\d{2}:?\d{2})?$/i', $buf, $matches)) {
            $tz = $matches[8] ?? null;
            $tzObj = $this->localTz;
            if ($tz !== null) {
                if (strtoupper($tz) === 'Z') {
                    $tzObj = new DateTimeZone('UTC');
                } else {
                    $tzObj = TimezoneData::getTimezone($tz) ?? $this->localTz;
                }
            }
            return new DateTimeImmutable(sprintf('%d-%02d-%02d %02d:%02d:%02d', (int)$matches[1], (int)$matches[2], (int)$matches[3], (int)$matches[4], (int)$matches[5], (int)$matches[6]), $tzObj);
        }
        if (preg_match('/^(\d{4})-(\d{2})-(\d{2})$/', $buf, $matches)) {
            return new DateTimeImmutable(sprintf('%d-%02d-%02d', (int)$matches[1], (int)$matches[2], (int)$matches[3]), $this->localTz);
        }
        return null;
    }

    private function parseRelativeWithTime(): ?DateTimeImmutable
    {
        $saved = $this->pos;
        $simpleRelative = ['today' => 0, 'yesterday' => -1, 'tomorrow' => 1];
        $tok1 = $this->peek();
        if ($tok1->type === TokenType::WORD && isset($simpleRelative[$tok1->value])) {
            $this->advance();
            $dayOffset = $simpleRelative[$tok1->value];
            if ($this->peek()->type === TokenType::TIME) {
                $timeTok = $this->advance();
                $timeParsed = self::parseTime($timeTok->value);
                if ($timeParsed !== null) {
                    [$hour, $minute] = $timeParsed;
                    $targetDate = (clone $this->now)->modify(($dayOffset >= 0 ? '+' : '') . $dayOffset . ' days');
                    return new DateTimeImmutable(sprintf('%d-%02d-%02d %02d:%02d:00', $targetDate->format('Y'), $targetDate->format('m'), $targetDate->format('d'), $hour, $minute), $this->localTz);
                }
            }
        }
        $this->pos = $saved;

        $tok1 = $this->peek();
        if ($tok1->type === TokenType::MODIFIER) {
            $this->advance();
            $modifier = $tok1->value;
            if ($this->peek()->type === TokenType::DAY) {
                $dayTok = $this->advance();
                $targetDay = self::DAYS[$dayTok->value];
                if ($this->peek()->type === TokenType::TIME) {
                    $timeTok = $this->advance();
                    $timeParsed = self::parseTime($timeTok->value);
                    if ($timeParsed !== null) {
                        [$hour, $minute] = $timeParsed;
                        $phpWeekday = (int)$this->now->format('N') - 1;
                        $daysAhead = $targetDay - $phpWeekday;
                        if ($modifier === 'next') {
                            if ($daysAhead <= 0) {
                                $daysAhead += 7;
                            }
                        } else {
                            if ($daysAhead >= 0) {
                                $daysAhead -= 7;
                            }
                        }
                        $targetDate = (clone $this->now)->modify(sprintf('%+d days', $daysAhead));
                        return new DateTimeImmutable(sprintf('%d-%02d-%02d %02d:%02d:00', $targetDate->format('Y'), $targetDate->format('m'), $targetDate->format('d'), $hour, $minute), $this->localTz);
                    }
                }
            }
        }
        $this->pos = $saved;

        if ($this->peek()->type === TokenType::DAY) {
            $dayTok = $this->advance();
            $targetDay = self::DAYS[$dayTok->value];
            if ($this->peek()->type === TokenType::TIME) {
                $timeTok = $this->advance();
                $timeParsed = self::parseTime($timeTok->value);
                if ($timeParsed !== null) {
                    [$hour, $minute] = $timeParsed;
                    $phpWeekday = (int)$this->now->format('N') - 1;
                    $daysAhead = $targetDay - $phpWeekday;
                    if ($daysAhead <= 0) {
                        $daysAhead += 7;
                    }
                    $targetDate = (clone $this->now)->modify(sprintf('%+d days', $daysAhead));
                    return new DateTimeImmutable(sprintf('%d-%02d-%02d %02d:%02d:00', $targetDate->format('Y'), $targetDate->format('m'), $targetDate->format('d'), $hour, $minute), $this->localTz);
                }
            }
        }
        $this->pos = $saved;
        return null;
    }

    private function parseDayAtTime(): ?DateTimeImmutable
    {
        $saved = $this->pos;
        $modifier = null;
        $tok1 = $this->peek();
        if ($tok1->type === TokenType::MODIFIER) {
            $modifier = $tok1->value;
            $this->advance();
        }
        $dayTok = $this->peek();
        if ($dayTok->type !== TokenType::DAY) {
            $this->pos = $saved;
            return null;
        }
        $this->advance();
        $targetDay = self::DAYS[$dayTok->value];
        $atTok = $this->peek();
        if ($atTok->type !== TokenType::AT) {
            $this->pos = $saved;
            return null;
        }
        $this->advance();
        $timeTok = $this->peek();
        if ($timeTok->type !== TokenType::TIME) {
            $this->pos = $saved;
            return null;
        }
        $this->advance();
        $timeParsed = self::parseTime($timeTok->value);
        if ($timeParsed === null) {
            $this->pos = $saved;
            return null;
        }
        [$hour, $minute] = $timeParsed;
        $phpWeekday = (int)$this->now->format('N') - 1;
        $daysAhead = $targetDay - $phpWeekday;
        if ($modifier === 'next') {
            if ($daysAhead <= 0) {
                $daysAhead += 7;
            }
        } elseif ($modifier === 'last' || $modifier === 'previous') {
            if ($daysAhead >= 0) {
                $daysAhead -= 7;
            }
        } else {
            if ($daysAhead <= 0) {
                $daysAhead += 7;
            }
        }
        $targetDate = (clone $this->now)->modify(sprintf('%+d days', $daysAhead));
        return new DateTimeImmutable(sprintf('%d-%02d-%02d %02d:%02d:00', $targetDate->format('Y'), $targetDate->format('m'), $targetDate->format('d'), $hour, $minute), $this->localTz);
    }

    private function parseOrdinalWithRelative(): ?DateTimeImmutable
    {
        $saved = $this->pos;
        $ordinalTok = $this->peek();
        if ($ordinalTok->type !== TokenType::ORDINAL) {
            return null;
        }
        $this->advance();
        $dayTok = $this->peek();
        if ($dayTok->type !== TokenType::DAY) {
            $this->pos = $saved;
            return null;
        }
        $this->advance();
        $targetDay = self::DAYS[$dayTok->value];
        $modifierTok = $this->peek();
        if ($modifierTok->type !== TokenType::MODIFIER || !in_array($modifierTok->value, ['next', 'last'], true)) {
            $this->pos = $saved;
            return null;
        }
        $this->advance();
        $modifier = $modifierTok->value;
        $unitTok = $this->peek();
        if ($unitTok->type !== TokenType::UNIT || !in_array($unitTok->value, ['month', 'year', 'week'], true)) {
            $this->pos = $saved;
            return null;
        }
        $this->advance();
        $unit = $unitTok->value;
        $yearTok = $this->peek();
        $year = $yearTok->type === TokenType::NUMBER && strlen($yearTok->value) === 4 ? (int)$yearTok->value : (int)$this->now->format('Y');
        if ($yearTok->type === TokenType::NUMBER && strlen($yearTok->value) === 4) {
            $this->advance();
        }

        $ordinal = self::ORDINALS[$ordinalTok->value] ?? 1;
        $month = (int)$this->now->format('m');
        if ($unit === 'month') {
            $month = $month + ($modifier === 'next' ? 1 : -1);
            $year = (int)$this->now->format('Y');
            while ($month > 12) {
                $month -= 12;
                $year++;
            }
            while ($month < 1) {
                $month += 12;
                $year--;
            }
        } elseif ($unit === 'year') {
            $year = $year + ($modifier === 'next' ? 1 : -1);
            $month = (int)$this->now->format('m');
        }
        $count = 0;
        $maxDay = (int)date('t', mktime(0, 0, 0, $month, 1, $year));
        for ($d = 1; $d <= $maxDay; $d++) {
            $dt = mktime(0, 0, 0, $month, $d, $year);
            if (date('N', $dt) === strval($targetDay + 1)) {
                $count++;
                if ($count === $ordinal) {
                    return new DateTimeImmutable(sprintf('%d-%02d-%02d %02d:%02d:%02d', $year, $month, $d, $this->now->format('H'), $this->now->format('i'), $this->now->format('s')), $this->localTz);
                }
            }
        }
        throw new DateParseError("No {$ordinalTok->value} {$dayTok->value} in {$month}/{$year}");
    }

    private function parseRelativeOffset(): ?DateTimeImmutable
    {
        $buf = $this->reconstruct();
        if (preg_match('/^([+-]?\s*)?(\d+)\s+(days?|weeks?|months?|hours?|minutes?|seconds?)\s*(ago|from now)?$/', $buf, $matches)) {
            $signStr = trim($matches[1] ?? '');
            $amount = (int)$matches[2];
            $unit = $matches[3] ?? '';
            $direction = $matches[4] ?? '';
            $sign = ($signStr === '-' || $direction === 'ago') ? -1 : 1;
            $amount *= $sign;
            if (in_array($unit, ['day', 'days'], true)) {
                return (clone $this->now)->modify(sprintf('%+d days', $amount));
            }
            if (in_array($unit, ['week', 'weeks'], true)) {
                return (clone $this->now)->modify(sprintf('%+d weeks', $amount));
            }
            if (in_array($unit, ['hour', 'hours'], true)) {
                return (clone $this->now)->modify(sprintf('%+d hours', $amount));
            }
            if (in_array($unit, ['minute', 'minutes'], true)) {
                return (clone $this->now)->modify(sprintf('%+d minutes', $amount));
            }
            if (in_array($unit, ['second', 'seconds'], true)) {
                return (clone $this->now)->modify(sprintf('%+d seconds', $amount));
            }
            if (in_array($unit, ['month', 'months'], true)) {
                return $this->addMonths($this->now, $amount);
            }
        }
        return null;
    }

    private function addMonths(DateTimeImmutable $date, int $months): DateTimeImmutable
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
        return new DateTimeImmutable(sprintf('%d-%02d-%02d %02d:%02d:%02d', $year, $month, $day, $date->format('H'), $date->format('i'), $date->format('s')), $date->getTimezone());
    }

    private function parseRelativeDay(): ?DateTimeImmutable
    {
        $saved = $this->pos;
        $tok1 = $this->peek();
        if ($tok1->type === TokenType::MODIFIER) {
            $this->advance();
            $modifier = $tok1->value;
            if ($this->peek()->type === TokenType::DAY) {
                $dayTok = $this->advance();
                $targetDay = self::DAYS[$dayTok->value];
                $phpWeekday = (int)$this->now->format('N') - 1;
                $daysAhead = $targetDay - $phpWeekday;
                if ($modifier === 'next') {
                    if ($daysAhead <= 0) {
                        $daysAhead += 7;
                    }
                } else {
                    if ($daysAhead >= 0) {
                        $daysAhead -= 7;
                    }
                }
                return (clone $this->now)->modify(sprintf('%+d days', $daysAhead));
            }
        }
        $this->pos = $saved;
        $tok1 = $this->peek();
        if ($tok1->type === TokenType::DAY) {
            $dayTok = $this->advance();
            $targetDay = self::DAYS[$dayTok->value];
            $phpWeekday = (int)$this->now->format('N') - 1;
            $daysAhead = $targetDay - $phpWeekday;
            if ($daysAhead <= 0) {
                $daysAhead += 7;
            }
            return (clone $this->now)->modify(sprintf('%+d days', $daysAhead));
        }
        $this->pos = $saved;
        return null;
    }

    private function parseOrdinalDay(): ?DateTimeImmutable
    {
        $saved = $this->pos;
        $buf = $this->reconstructSep();

        if (preg_match('/^(\d+(?:st|nd|rd|th)?|first|second|third|fourth|fifth)\s+(monday|tuesday|wednesday|thursday|friday|saturday|sunday|mon|tue|wed|thu|fri|sat|sun)\s+(?:of\s+)?(?:(january|february|march|april|may|june|july|august|september|october|november|december|jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\s*)?(\d{4})?$/i', $buf, $matches)) {
            $ordinalStr = $matches[1];
            $dayName = $matches[2];
            $monthStr = $matches[3] ?? null;
            $yearStr = $matches[4] ?? null;

            if (preg_match('/^\d+/', $ordinalStr, $om)) {
                $ordinal = (int)$om[0];
            } else {
                $ordinal = self::ORDINALS[strtolower($ordinalStr)] ?? 1;
            }

            $targetDay = self::DAYS[strtolower($dayName)];
            $month = $monthStr !== null ? self::MONTHS[strtolower($monthStr)] : (int)$this->now->format('m');
            $year = $yearStr !== null ? (int)$yearStr : (int)$this->now->format('Y');

            $count = 0;
            $maxDay = (int)date('t', mktime(0, 0, 0, $month, 1, $year));
            for ($d = 1; $d <= $maxDay; $d++) {
                $dt = mktime(0, 0, 0, $month, $d, $year);
                if (date('N', $dt) === strval($targetDay + 1)) {
                    $count++;
                    if ($count === $ordinal) {
                        return new DateTimeImmutable(sprintf('%d-%02d-%02d %02d:%02d:%02d', $year, $month, $d, $this->now->format('H'), $this->now->format('i'), $this->now->format('s')), $this->localTz);
                    }
                }
            }

            throw new DateParseError("No {$ordinalStr} {$dayName} in {$month}/{$year}");
        }

        if (preg_match('/^final\s+(monday|tuesday|wednesday|thursday|friday|saturday|sunday|mon|tue|wed|thu|fri|sat|sun)\s+(?:of\s+)?(?:(january|february|march|april|may|june|july|august|september|october|november|december|jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\s*)?(\d{4})?$/i', $buf, $matches)) {
            $dayName = $matches[1];
            $monthStr = $matches[2] ?? null;
            $yearStr = $matches[3] ?? null;

            $targetDay = self::DAYS[strtolower($dayName)];
            $month = $monthStr !== null ? self::MONTHS[strtolower($monthStr)] : (int)$this->now->format('m');
            $year = $yearStr !== null ? (int)$yearStr : (int)$this->now->format('Y');

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
                return new DateTimeImmutable(sprintf('%d-%02d-%02d %02d:%02d:%02d', $year, $month, $lastOccurrence, $this->now->format('H'), $this->now->format('i'), $this->now->format('s')), $this->localTz);
            }

            throw new DateParseError("No {$dayName} in {$month}/{$year}");
        }

        $this->pos = $saved;
        return null;
    }

    private function parseRelativeUnit(): ?DateTimeImmutable
    {
        $saved = $this->pos;
        $simpleMapping = ['today' => 0, 'yesterday' => -1, 'tomorrow' => 1, 'now' => 0];
        $buf = $this->reconstruct();
        if (isset($simpleMapping[$buf])) {
            return (clone $this->now)->modify(sprintf('%+d days', $simpleMapping[$buf]));
        }
        if (preg_match('/^(next|last|previous)\s+(week|month|year)$/i', $buf, $matches)) {
            [, $direction, $unit] = $matches;
            if ($unit === 'week') {
                $days = strtolower($direction) === 'next' ? 7 : -7;
                return (clone $this->now)->modify(sprintf('%+d days', $days));
            }
            if ($unit === 'month') {
                $months = strtolower($direction) === 'next' ? 1 : -1;
                return $this->addMonths($this->now, $months);
            }
            if ($unit === 'year') {
                $years = strtolower($direction) === 'next' ? 1 : -1;
                return (clone $this->now)->modify(sprintf('%+d years', $years));
            }
        }
        $this->pos = $saved;
        return null;
    }

    private function parseDaysUntil(): ?DateInterval
    {
        $saved = $this->pos;
        $buf = $this->reconstruct();
        if (preg_match('/^days?\s+until\s+(.+)$/i', $buf, $matches)) {
            $dateExpr = trim($matches[1]);
            $targetDate = self::getdateWithLexer($dateExpr);
            if ($targetDate !== null) {
                return $this->now->diff($targetDate);
            }
        }
        $this->pos = $saved;
        return null;
    }

    private function parseDaysSince(): ?DateInterval
    {
        $saved = $this->pos;
        $buf = $this->reconstruct();
        if (preg_match('/^days?\s+since\s+(.+)$/i', $buf, $matches)) {
            $dateExpr = trim($matches[1]);
            $targetDate = self::getdateWithLexer($dateExpr);
            if ($targetDate !== null) {
                return $targetDate->diff($this->now);
            }
        }
        $this->pos = $saved;
        return null;
    }

    private function parse24HourTime(): ?DateTimeImmutable
    {
        $saved = $this->pos;
        $tok = $this->peek();
        if ($tok->type !== TokenType::TIME) {
            return null;
        }
        $timeVal = $tok->value;
        if (strpos($timeVal, ':') === false) {
            return null;
        }
        $peekTok = $this->tokens[$this->pos + 1] ?? null;
        if ($peekTok !== null && $peekTok->type === TokenType::TIME && in_array($peekTok->value, ['am', 'pm', 'a', 'p'], true)) {
            return null;
        }
        $this->advance();
        if (!preg_match('/^(\d{1,2}):(\d{2})(?::(\d{2}))?$/', $timeVal, $matches)) {
            $this->pos = $saved;
            return null;
        }
        $hour = (int)$matches[1];
        $minute = (int)$matches[2];
        $second = isset($matches[3]) ? (int)$matches[3] : 0;
        if ($hour > 23 || $minute > 59 || $second > 59) {
            $this->pos = $saved;
            return null;
        }
        return new DateTimeImmutable(sprintf('%d-%02d-%02d %02d:%02d:%02d', $this->now->format('Y'), $this->now->format('m'), $this->now->format('d'), $hour, $minute, $second), $this->localTz);
    }

    private function parse12HourTime(): ?DateTimeImmutable
    {
        $saved = $this->pos;
        $tok = $this->peek();
        if ($tok->type !== TokenType::TIME) {
            return null;
        }
        $timeVal = $tok->value;
        if (strpos($timeVal, ':') === false) {
            return null;
        }
        $ampmTok = $this->tokens[$this->pos + 1] ?? null;
        $ampm = null;
        if ($ampmTok !== null && $ampmTok->type === TokenType::TIME && in_array($ampmTok->value, ['am', 'pm', 'a', 'p'], true)) {
            $ampm = strtolower($ampmTok->value);
            $this->advance();
        }
        if ($ampm === null) {
            return null;
        }
        $this->advance();
        if (!preg_match('/^(\d{1,2}):(\d{2}):(\d{2})$/', $timeVal, $matches)) {
            $this->pos = $saved;
            return null;
        }
        $hour = (int)$matches[1];
        $minute = (int)$matches[2];
        $second = (int)$matches[3];
        if (in_array($ampm, ['pm', 'p']) && $hour !== 12) {
            $hour += 12;
        } elseif (in_array($ampm, ['am', 'a']) && $hour === 12) {
            $hour = 0;
        }
        if ($hour > 23 || $minute > 59 || $second > 59) {
            $this->pos = $saved;
            return null;
        }
        return new DateTimeImmutable(sprintf('%d-%02d-%02d %02d:%02d:%02d', $this->now->format('Y'), $this->now->format('m'), $this->now->format('d'), $hour, $minute, $second), $this->localTz);
    }

    private function parseShort12HourTime(): ?DateTimeImmutable
    {
        $saved = $this->pos;
        $tok = $this->peek();
        if ($tok->type !== TokenType::NUMBER) {
            return null;
        }
        $numVal = $tok->value;
        if (strlen($numVal) < 3 || strlen($numVal) > 4) {
            return null;
        }
        $ampmTok = $this->tokens[$this->pos + 1] ?? null;
        $ampm = null;
        if ($ampmTok !== null && $ampmTok->type === TokenType::TIME && in_array($ampmTok->value, ['am', 'pm', 'a', 'p'], true)) {
            $ampm = strtolower($ampmTok->value);
            $this->advance();
        }
        if ($ampm === null) {
            return null;
        }
        $this->advance();
        if (strlen($numVal) === 4) {
            $hour = (int)substr($numVal, 0, 2);
            $minute = (int)substr($numVal, 2, 2);
        } else {
            $hour = (int)$numVal[0];
            $minute = (int)substr($numVal, 1, 2);
        }
        if (in_array($ampm, ['pm', 'p']) && $hour !== 12) {
            $hour += 12;
        } elseif (in_array($ampm, ['am', 'a']) && $hour === 12) {
            $hour = 0;
        }
        if ($hour > 23 || $minute > 59) {
            $this->pos = $saved;
            return null;
        }
        return new DateTimeImmutable(sprintf('%d-%02d-%02d %02d:%02d:00', $this->now->format('Y'), $this->now->format('m'), $this->now->format('d'), $hour, $minute), $this->localTz);
    }

    private function reconstruct(): string
    {
        $buf = '';
        foreach ($this->tokens as $tok) {
            if ($tok->type === TokenType::EOF) {
                break;
            }
            if ($buf !== '' && !in_array($tok->type, [TokenType::DATE_SEPARATOR, TokenType::TIME_SEPARATOR], true)) {
                $buf .= ' ';
            }
            $buf .= $tok->value;
        }
        return $buf;
    }

    private function reconstructSep(): string
    {
        $buf = '';
        $prevType = null;
        foreach ($this->tokens as $tok) {
            if ($tok->type === TokenType::EOF) {
                break;
            }
            if ($buf !== '') {
                $isSep = in_array($tok->type, [TokenType::DATE_SEPARATOR, TokenType::TIME_SEPARATOR], true);
                $prevSep = $prevType !== null && in_array($prevType, [TokenType::DATE_SEPARATOR, TokenType::TIME_SEPARATOR], true);
                if (!$isSep && !$prevSep) {
                    $buf .= ' ';
                }
            }
            $buf .= $tok->value;
            $prevType = $tok->type;
        }
        return $buf;
    }

    private function reconstructComma(): string
    {
        $buf = '';
        $prevType = null;
        foreach ($this->tokens as $tok) {
            if ($tok->type === TokenType::EOF) {
                break;
            }
            if ($buf !== '') {
                $isSep = $tok->type === TokenType::DATE_SEPARATOR;
                $isComma = $tok->type === TokenType::COMMA;
                $prevSep = $prevType === TokenType::DATE_SEPARATOR;
                $prevComma = $prevType === TokenType::COMMA;
                if (!$isSep && !$isComma && !$prevSep && !$prevComma && $tok->type !== TokenType::TIMEZONE && $prevType !== TokenType::TIMEZONE) {
                    $buf .= ' ';
                }
            }
            $buf .= $tok->value;
            $prevType = $tok->type;
        }
        return $buf;
    }

    private function reconstructWithTimezone(): string
    {
        $buf = '';
        $prevType = null;
        foreach ($this->tokens as $tok) {
            if ($tok->type === TokenType::EOF) {
                break;
            }
            if ($buf !== '') {
                $addSpace = true;
                if ($tok->type === TokenType::DATE_SEPARATOR) {
                    $addSpace = false;
                } elseif ($prevType === TokenType::DATE_SEPARATOR) {
                    $addSpace = false;
                } elseif ($tok->type === TokenType::TIME_SEPARATOR) {
                    $addSpace = false;
                } elseif ($prevType === TokenType::TIME_SEPARATOR) {
                    $addSpace = false;
                } elseif ($tok->type === TokenType::TIMEZONE && $prevType === TokenType::TIME) {
                    $addSpace = false;
                } elseif ($tok->type === TokenType::TIMEZONE) {
                    $addSpace = false;
                }
                if ($addSpace) {
                    $buf .= ' ';
                }
            }
            $buf .= $tok->value;
            $prevType = $tok->type;
        }
        return $buf;
    }

    public static function getdateWithLexer(string $buf): ?DateTimeImmutable
    {
        if ($buf === null || $buf === '') {
            return null;
        }
        $buf = trim($buf);
        if ($buf === '') {
            return null;
        }
        $lexer = new Lexer();
        $tokens = $lexer->tokenize($buf);
        $parser = new self($tokens);
        return $parser->parse();
    }

    public function debugReconstruct(): string
    {
        return $this->reconstructWithTimezone();
    }
}