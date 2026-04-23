use lib 'lib';
use strict;
use warnings;

use Getdate::Getdate;
use Getdate::DateTime;
use Getdate::DateInterval;

my $tests = 0;
my $passed = 0;

sub test_ok {
    my ($cond, $desc) = @_;
    $tests++;
    if ($cond) {
        $passed++;
        print "ok $tests - $desc\n";
    } else {
        print "not ok $tests - $desc\n";
    }
}

sub test_is {
    my ($got, $expected, $desc) = @_;
    $tests++;
    if ($got eq $expected) {
        $passed++;
        print "ok $tests - $desc\n";
    } else {
        print "not ok $tests - $desc (got: $got, expected: $expected)\n";
    }
}

my $now = Getdate::DateTime->now;

# Test basic expressions
test_ok(defined Getdate::Getdate::getdate("now"), "now defined");
test_ok(ref(Getdate::Getdate::getdate("now")) eq 'Getdate::DateTime', "now returns DateTime");

my $today = Getdate::Getdate::getdate("today");
test_ok(defined $today, "today defined");
test_is($today->year, $now->year, "today year");
test_is($today->month, $now->month, "today month");
test_is($today->day, $now->day, "today day");

my $yesterday = Getdate::Getdate::getdate("yesterday");
test_ok(defined $yesterday, "yesterday defined");
my $expected_yesterday = $now->add({days => -1});
test_is($yesterday->year, $expected_yesterday->year, "yesterday year");

my $tomorrow = Getdate::Getdate::getdate("tomorrow");
test_ok(defined $tomorrow, "tomorrow defined");
my $expected_tomorrow = $now->add({days => 1});
test_is($tomorrow->year, $expected_tomorrow->year, "tomorrow year");

test_ok(defined Getdate::Getdate::getdate("+2 days"), "+2 days defined");
test_ok(defined Getdate::Getdate::getdate("-3 days"), "-3 days defined");
test_ok(defined Getdate::Getdate::getdate("3 days ago"), "3 days ago defined");
test_ok(defined Getdate::Getdate::getdate("72 hours from now"), "72 hours from now defined");
test_ok(defined Getdate::Getdate::getdate("next week"), "next week defined");
test_ok(defined Getdate::Getdate::getdate("last week"), "last week defined");
test_ok(defined Getdate::Getdate::getdate("next month"), "next month defined");

my $next_year = Getdate::Getdate::getdate("next year");
test_ok(defined $next_year, "next year defined");
test_is($next_year->year, $now->year + 1, "next year is current year + 1");

my $next_thursday = Getdate::Getdate::getdate("next thursday");
test_ok(defined $next_thursday, "next thursday defined");
test_is($next_thursday->weekday, 3, "next thursday is Thursday (weekday=3)");

my $last_friday = Getdate::Getdate::getdate("last friday");
test_ok(defined $last_friday, "last friday defined");
test_is($last_friday->weekday, 4, "last friday is Friday (weekday=4)");

my $ordinal = Getdate::Getdate::getdate("2nd wednesday of march 2026");
test_ok(defined $ordinal, "2nd wednesday of march 2026 defined");
if ($ordinal) {
    test_is($ordinal->year, 2026, "2nd wednesday year");
    test_is($ordinal->month, 3, "2nd wednesday month");
    test_is($ordinal->weekday, 2, "2nd wednesday is Wednesday (weekday=2)");
}

my $ordinal_no_year = Getdate::Getdate::getdate("1st monday of march");
test_ok(defined $ordinal_no_year, "1st monday of march defined");
if ($ordinal_no_year) {
    test_is($ordinal_no_year->month, 3, "1st monday month");
    test_is($ordinal_no_year->weekday, 0, "1st monday is Monday (weekday=0)");
}

my $final = Getdate::Getdate::getdate("final friday of march 2026");
test_ok(defined $final, "final friday of march 2026 defined");
if ($final) {
    test_is($final->year, 2026, "final friday year");
    test_is($final->month, 3, "final friday month");
    test_is($final->weekday, 4, "final friday is Friday (weekday=4)");
}

my $iso = Getdate::Getdate::getdate("2026-03-06");
test_ok(defined $iso, "ISO date 2026-03-06 defined");
if ($iso) {
    test_is($iso->year, 2026, "ISO date year");
    test_is($iso->month, 3, "ISO date month");
    test_is($iso->day, 6, "ISO date day");
}

my $iso_dt = Getdate::Getdate::getdate("2026-03-06T14:30:00Z");
test_ok(defined $iso_dt, "ISO datetime defined");
if ($iso_dt) {
    test_is($iso_dt->year, 2026, "ISO datetime year");
    test_is($iso_dt->month, 3, "ISO datetime month");
    test_is($iso_dt->day, 6, "ISO datetime day");
    test_is($iso_dt->hour, 14, "ISO datetime hour");
    test_is($iso_dt->minute, 30, "ISO datetime minute");
}

my $compact = Getdate::Getdate::getdate("202603062145");
test_ok(defined $compact, "Compact 202603062145 defined");
if ($compact) {
    test_is($compact->year, 2026, "compact year");
    test_is($compact->month, 3, "compact month");
    test_is($compact->day, 6, "compact day");
    test_is($compact->hour, 21, "compact hour");
    test_is($compact->minute, 45, "compact minute");
}

my $us = Getdate::Getdate::getdate("3/5/2026 21:45");
test_ok(defined $us, "US datetime defined");
if ($us) {
    test_is($us->month, 3, "US datetime month");
    test_is($us->day, 5, "US datetime day");
    test_is($us->year, 2026, "US datetime year");
}

my $us_ampm = Getdate::Getdate::getdate("3/5/2026 9:45p");
test_ok(defined $us_ampm, "US datetime with am/pm defined");
if ($us_ampm) {
    test_is($us_ampm->hour, 21, "US datetime am/pm hour");
}

my $unix = Getdate::Getdate::getdate("1741305270");
test_ok(defined $unix, "Unix timestamp defined");
if ($unix) {
    test_is($unix->year, 2025, "Unix timestamp year");
}

test_ok(Getdate::Getdate::verify_valid_date_expression("tomorrow"), "verify tomorrow");
test_ok(!Getdate::Getdate::verify_valid_date_expression("not a date"), "verify invalid");

my $days_until = Getdate::Getdate::getdate("days until 2nd wednesday april 2026");
test_ok(defined $days_until && ref($days_until) eq 'Getdate::DateInterval', "days until defined");

my $days_since = Getdate::Getdate::getdate("days since 2nd wednesday march 2026");
test_ok(defined $days_since && ref($days_since) eq 'Getdate::DateInterval', "days since defined");

my $di = Getdate::Getdate::getdate("days until 2nd wednesday april 2027");
if ($di && ref($di) eq 'Getdate::DateInterval') {
    my $formatted = $di->format("%a days");
    test_ok($formatted =~ /^\d+ days$/, "date interval format works: $formatted");
} else {
    test_ok(0, "days until returned DateInterval");
}

print "\nAll tests completed: $passed/$tests passed.\n";
