<?php

declare(strict_types=1);

namespace GetdateNext\Tests;

use DateInterval;
use DateTimeImmutable;
use PHPUnit\Framework\TestCase;
use GetdateNext\Getdate;
use GetdateNext\DateParseError;

class GetdateTest extends TestCase
{
    public function testNow(): void
    {
        $result = Getdate::getdate('now');
        $this->assertNotNull($result);
        $this->assertInstanceOf(DateTimeImmutable::class, $result);
    }

    public function testToday(): void
    {
        $result = Getdate::getdate('today');
        $this->assertNotNull($result);
        $now = new DateTimeImmutable();
        $this->assertEquals($now->format('Y-m-d'), $result->format('Y-m-d'));
    }

    public function testYesterday(): void
    {
        $result = Getdate::getdate('yesterday');
        $this->assertNotNull($result);
        $expected = (new DateTimeImmutable())->modify('-1 day');
        $this->assertEquals($expected->format('Y-m-d'), $result->format('Y-m-d'));
    }

    public function testTomorrow(): void
    {
        $result = Getdate::getdate('tomorrow');
        $this->assertNotNull($result);
        $expected = (new DateTimeImmutable())->modify('+1 day');
        $this->assertEquals($expected->format('Y-m-d'), $result->format('Y-m-d'));
    }

    public function testPlusDays(): void
    {
        $result = Getdate::getdate('+2 days');
        $this->assertNotNull($result);
        $expected = (new DateTimeImmutable())->modify('+2 days');
        $this->assertEquals($expected->format('Y-m-d'), $result->format('Y-m-d'));
    }

    public function testMinusDays(): void
    {
        $result = Getdate::getdate('-3 days');
        $this->assertNotNull($result);
        $expected = (new DateTimeImmutable())->modify('-3 days');
        $this->assertEquals($expected->format('Y-m-d'), $result->format('Y-m-d'));
    }

    public function testDaysAgo(): void
    {
        $result = Getdate::getdate('3 days ago');
        $this->assertNotNull($result);
        $expected = (new DateTimeImmutable())->modify('-3 days');
        $this->assertEquals($expected->format('Y-m-d'), $result->format('Y-m-d'));
    }

    public function testHoursFromNow(): void
    {
        $result = Getdate::getdate('72 hours from now');
        $this->assertNotNull($result);
        $expected = (new DateTimeImmutable())->modify('+72 hours');
        $diff = abs($result->getTimestamp() - $expected->getTimestamp());
        $this->assertLessThan(2, $diff);
    }

    public function testNextWeek(): void
    {
        $result = Getdate::getdate('next week');
        $this->assertNotNull($result);
        $expected = (new DateTimeImmutable())->modify('+1 week');
        $diff = abs($result->getTimestamp() - $expected->getTimestamp());
        $this->assertLessThan(2, $diff);
    }

    public function testLastWeek(): void
    {
        $result = Getdate::getdate('last week');
        $this->assertNotNull($result);
        $expected = (new DateTimeImmutable())->modify('-1 week');
        $diff = abs($result->getTimestamp() - $expected->getTimestamp());
        $this->assertLessThan(2, $diff);
    }

    public function testNextMonth(): void
    {
        $result = Getdate::getdate('next month');
        $this->assertNotNull($result);
    }

    public function testNextYear(): void
    {
        $result = Getdate::getdate('next year');
        $this->assertNotNull($result);
        $now = new DateTimeImmutable();
        $this->assertEquals($now->format('Y') + 1, $result->format('Y'));
    }

    public function testNextThursday(): void
    {
        $result = Getdate::getdate('next thursday');
        $this->assertNotNull($result);
        $this->assertEquals(4, $result->format('N'));
        $now = new DateTimeImmutable();
        $daysAhead = $result->diff(new DateTimeImmutable($now->format('Y-m-d')))->days;
        $this->assertGreaterThan(0, $daysAhead);
        $this->assertLessThanOrEqual(7, $daysAhead);
    }

    public function testLastFriday(): void
    {
        $result = Getdate::getdate('last friday');
        $this->assertNotNull($result);
        $this->assertEquals(5, $result->format('N'));
        $now = new DateTimeImmutable();
        $daysDiff = (new DateTimeImmutable($now->format('Y-m-d')))->diff($result)->days;
        $this->assertGreaterThan(0, $daysDiff);
        $this->assertLessThanOrEqual(7, $daysDiff);
    }

    public function testOrdinalDay(): void
    {
        $result = Getdate::getdate('2nd wednesday of march 2026');
        $this->assertNotNull($result);
        $this->assertEquals(2026, $result->format('Y'));
        $this->assertEquals(3, $result->format('m'));
        $this->assertEquals(3, $result->format('N'));
    }

    public function testOrdinalDayNoYear(): void
    {
        $result = Getdate::getdate('1st monday of march');
        $this->assertNotNull($result);
        $this->assertEquals(3, $result->format('m'));
        $this->assertEquals(1, $result->format('N'));
    }

    public function testFinalFriday(): void
    {
        $result = Getdate::getdate('final friday of march 2026');
        $this->assertNotNull($result);
        $this->assertEquals(2026, $result->format('Y'));
        $this->assertEquals(3, $result->format('m'));
        $this->assertEquals(5, $result->format('N'));
    }

    public function testIsoDate(): void
    {
        $result = Getdate::getdate('2026-03-06');
        $this->assertNotNull($result);
        $this->assertEquals(2026, $result->format('Y'));
        $this->assertEquals(3, $result->format('m'));
        $this->assertEquals(6, $result->format('d'));
    }

    public function testIso8601WithUtcZ(): void
    {
        $result = Getdate::getdate('2026-03-06T14:30:00Z');
        $this->assertNotNull($result);
        $this->assertEquals(2026, $result->format('Y'));
        $this->assertEquals(3, $result->format('m'));
        $this->assertEquals(6, $result->format('d'));
        $this->assertEquals(14, $result->format('H'));
        $this->assertEquals(30, $result->format('i'));
    }

    public function testIso8601WithPlus08Offset(): void
    {
        $result = Getdate::getdate('2026-03-06T14:30:00+08:00');
        $this->assertNotNull($result);
        $this->assertEquals(2026, $result->format('Y'));
        $this->assertEquals(3, $result->format('m'));
        $this->assertEquals(6, $result->format('d'));
        $this->assertEquals(14, $result->format('H'));
        $this->assertEquals(30, $result->format('i'));
        $offset = $result->getTimezone()->getOffset($result);
        $this->assertEquals(28800, $offset);
    }

    public function testIso8601WithMinus05Offset(): void
    {
        $result = Getdate::getdate('2026-03-06T14:30:00-05:00');
        $this->assertNotNull($result);
        $this->assertEquals(14, $result->format('H'));
        $offset = $result->getTimezone()->getOffset($result);
        $this->assertEquals(-18000, $offset);
    }

    public function testIso8601WithPlus08NoColon(): void
    {
        $result = Getdate::getdate('2026-03-06T14:30:00+0800');
        $this->assertNotNull($result);
        $this->assertEquals(14, $result->format('H'));
        $offset = $result->getTimezone()->getOffset($result);
        $this->assertEquals(28800, $offset);
    }

    public function testIso8601PreservesHourNotConverted(): void
    {
        $result = Getdate::getdate('2026-03-06T10:00:00+08:00');
        $this->assertNotNull($result);
        $this->assertEquals(10, $result->format('H'));
        $this->assertEquals(0, $result->format('i'));
    }

    public function testUsDateWithTime(): void
    {
        $result = Getdate::getdate('3/5/2026 21:45');
        $this->assertNotNull($result);
        $this->assertEquals(3, $result->format('m'));
        $this->assertEquals(5, $result->format('d'));
        $this->assertEquals(2026, $result->format('Y'));
        $this->assertEquals(21, $result->format('H'));
        $this->assertEquals(45, $result->format('i'));
    }

    public function testUsDateWith12HourPm(): void
    {
        $result = Getdate::getdate('3/5/2026 9:45p');
        $this->assertNotNull($result);
        $this->assertEquals(21, $result->format('H'));
    }

    public function testUsDateOnly(): void
    {
        $result = Getdate::getdate('03/06/2026');
        $this->assertNotNull($result);
        $this->assertEquals(3, $result->format('m'));
        $this->assertEquals(6, $result->format('d'));
        $this->assertEquals(2026, $result->format('Y'));
    }

    public function testCompactFormat(): void
    {
        $result = Getdate::getdate('202603062145');
        $this->assertNotNull($result);
        $this->assertEquals(2026, $result->format('Y'));
        $this->assertEquals(3, $result->format('m'));
        $this->assertEquals(6, $result->format('d'));
        $this->assertEquals(21, $result->format('H'));
        $this->assertEquals(45, $result->format('i'));
    }

    public function testVerifyValidDateExpressionTrue(): void
    {
        $this->assertTrue(Getdate::verifyValidDateExpression('now'));
        $this->assertTrue(Getdate::verifyValidDateExpression('next friday'));
        $this->assertTrue(Getdate::verifyValidDateExpression('2026-03-06'));
    }

    public function testVerifyValidDateExpressionFalse(): void
    {
        $this->assertFalse(Getdate::verifyValidDateExpression('invalid garbage'));
        $this->assertFalse(Getdate::verifyValidDateExpression('not a date'));
    }

    public function testReturnsFalseForInvalid(): void
    {
        $result = Getdate::getdate('invalid garbage');
        $this->assertNull($result);
    }

    public function testNullInput(): void
    {
        $this->assertNull(Getdate::getdate(null));
        $this->assertNull(Getdate::getdate(''));
    }

    public function testTomorrow2pm(): void
    {
        $result = Getdate::getdate('tomorrow 2pm');
        $this->assertNotNull($result);
        $expected = (new DateTimeImmutable())->modify('+1 day');
        $this->assertEquals($expected->format('Y-m-d'), $result->format('Y-m-d'));
        $this->assertEquals(14, $result->format('H'));
        $this->assertEquals(0, $result->format('i'));
    }

    public function testYesterday9am(): void
    {
        $result = Getdate::getdate('yesterday 9am');
        $this->assertNotNull($result);
        $expected = (new DateTimeImmutable())->modify('-1 day');
        $this->assertEquals($expected->format('Y-m-d'), $result->format('Y-m-d'));
        $this->assertEquals(9, $result->format('H'));
        $this->assertEquals(0, $result->format('i'));
    }

    public function testToday5pm(): void
    {
        $result = Getdate::getdate('today 5pm');
        $this->assertNotNull($result);
        $now = new DateTimeImmutable();
        $this->assertEquals($now->format('Y-m-d'), $result->format('Y-m-d'));
        $this->assertEquals(17, $result->format('H'));
        $this->assertEquals(0, $result->format('i'));
    }

    public function testFriday2pm(): void
    {
        $result = Getdate::getdate('friday 2pm');
        $this->assertNotNull($result);
        $this->assertEquals(5, $result->format('N'));
        $this->assertEquals(14, $result->format('H'));
        $this->assertEquals(0, $result->format('i'));
    }

    public function testThursday330pm(): void
    {
        $result = Getdate::getdate('thursday 3:30pm');
        $this->assertNotNull($result);
        $this->assertEquals(4, $result->format('N'));
        $this->assertEquals(15, $result->format('H'));
        $this->assertEquals(30, $result->format('i'));
    }

    public function testNextThursday2pm(): void
    {
        $result = Getdate::getdate('next thursday 2pm');
        $this->assertNotNull($result);
        $this->assertEquals(4, $result->format('N'));
        $this->assertEquals(14, $result->format('H'));
        $this->assertEquals(0, $result->format('i'));
    }

    public function testTomorrowNoon(): void
    {
        $result = Getdate::getdate('tomorrow noon');
        $this->assertNotNull($result);
        $expected = (new DateTimeImmutable())->modify('+1 day');
        $this->assertEquals($expected->format('Y-m-d'), $result->format('Y-m-d'));
        $this->assertEquals(12, $result->format('H'));
        $this->assertEquals(0, $result->format('i'));
    }

    public function testYesterdayMidnight(): void
    {
        $result = Getdate::getdate('yesterday midnight');
        $this->assertNotNull($result);
        $expected = (new DateTimeImmutable())->modify('-1 day');
        $this->assertEquals($expected->format('Y-m-d'), $result->format('Y-m-d'));
        $this->assertEquals(0, $result->format('H'));
        $this->assertEquals(0, $result->format('i'));
    }

    public function testNextFriday2pm(): void
    {
        $result = Getdate::getdate('next friday 2pm');
        $this->assertNotNull($result);
        $this->assertEquals(5, $result->format('N'));
        $this->assertEquals(14, $result->format('H'));
        $this->assertEquals(0, $result->format('i'));
    }

    public function testLastFriday2pm(): void
    {
        $result = Getdate::getdate('last friday 2pm');
        $this->assertNotNull($result);
        $this->assertEquals(5, $result->format('N'));
        $this->assertEquals(14, $result->format('H'));
        $this->assertEquals(0, $result->format('i'));
    }

    public function testDaysUntilOrdinal(): void
    {
        $result = Getdate::getdate('days until 2nd wednesday april 2026');
        $this->assertNotNull($result);
        $this->assertInstanceOf(DateInterval::class, $result);
        $totalDays = (int)$result->format('%a');
        $this->assertGreaterThanOrEqual(0, $totalDays);
    }

    public function testDaysUntilFinal(): void
    {
        $result = Getdate::getdate('days until final friday of may 2026');
        $this->assertNotNull($result);
        $this->assertInstanceOf(DateInterval::class, $result);
        $this->assertGreaterThan(0, $result->days);
    }

    public function testDaysUntilSimple(): void
    {
        $result = Getdate::getdate('days until next friday');
        $this->assertNotNull($result);
        $this->assertInstanceOf(DateInterval::class, $result);
        $this->assertGreaterThan(0, $result->days);
    }

    public function testDaysSincePast(): void
    {
        $result = Getdate::getdate('days since 2nd wednesday march 2026');
        $this->assertNotNull($result);
        $this->assertInstanceOf(DateInterval::class, $result);
        $this->assertGreaterThan(0, $result->days);
    }

    public function testDayUntilSingular(): void
    {
        $result = Getdate::getdate('day until next friday');
        $this->assertNotNull($result);
        $this->assertInstanceOf(DateInterval::class, $result);
        $this->assertGreaterThan(0, $result->days);
    }

    public function testGetdateTimestamp(): void
    {
        $result = Getdate::getdateTimestamp('next friday');
        $this->assertIsInt($result);
        $this->assertGreaterThan(time(), $result);
    }

    public function testDayNameAbbrev(): void
    {
        $result = Getdate::getdate('next mon');
        $this->assertNotNull($result);
        $this->assertEquals(1, $result->format('N'));
    }

    public function testMonthAbbrev(): void
    {
        $result = Getdate::getdate('1st monday of mar 2026');
        $this->assertNotNull($result);
        $this->assertEquals(3, $result->format('m'));
    }
}
