package Getdate::TimezoneData;

use strict;
use warnings;

our $VERSION = '0.01';

our %TIMEZONE_ABBREV_OFFSET = (
    est => -5,
    cst => -6,
    mst => -7,
    pst => -8,
    edt => -4,
    cdt => -5,
    mdt => -6,
    pdt => -7,
    gmt => 0,
    utc => 0,
    z  => 0,
    bst => 1,
    cet => 1,
    cest => 2,
    jst => 9,
    aest => 10,
    aedt => 11,
    nzst => 12,
    nzdt => 13,
);

our %ABBREV_TO_ZONE = (
    est => 'America/New_York',
    cst => 'America/Chicago',
    mst => 'America/Denver',
    pst => 'America/Los_Angeles',
    edt => 'America/New_York',
    cdt => 'America/Chicago',
    mdt => 'America/Denver',
    pdt => 'America/Los_Angeles',
    gmt => 'UTC',
    bst => 'Europe/London',
    cet => 'Europe/Paris',
    cest => 'Europe/Paris',
    jst => 'Asia/Tokyo',
    aest => 'Australia/Sydney',
    aedt => 'Australia/Sydney',
    nzst => 'Pacific/Auckland',
    nzdt => 'Pacific/Auckland',
);

sub get_timezone {
    my ($abbrev) = @_;
    
    $abbrev = lc($abbrev);
    return 'UTC' if $abbrev eq 'utc' || $abbrev eq 'z';
    
    my $zone = $ABBREV_TO_ZONE{$abbrev};
    return $zone if $zone;
    
    my $offset = $TIMEZONE_ABBREV_OFFSET{$abbrev};
    return $offset if defined $offset;
    
    return undef;
}

sub get_offset {
    my ($abbrev) = @_;
    
    $abbrev = lc($abbrev);
    return 0 if $abbrev eq 'utc' || $abbrev eq 'z' || $abbrev eq 'gmt';
    
    return $TIMEZONE_ABBREV_OFFSET{$abbrev};
}

1;
