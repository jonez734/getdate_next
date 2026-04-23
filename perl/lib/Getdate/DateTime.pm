package Getdate::DateTime;

use strict;
use warnings;
use Time::Local qw(timelocal timegm);

our $VERSION = '0.01';

sub new {
    my ($class, %params) = @_;
    
    my $year   = $params{year}   // 1970;
    my $month  = $params{month}  // 1;
    my $day    = $params{day}    // 1;
    my $hour   = $params{hour}   // 0;
    my $minute = $params{minute} // 0;
    my $second = $params{second} // 0;
    my $tz     = $params{tz};
    
    if ($month < 1 || $month > 12) {
        require Getdate::DateParseError;
        die Getdate::DateParseError->new("Month out of range: $month");
    }
    if ($day < 1 || $day > 31) {
        require Getdate::DateParseError;
        die Getdate::DateParseError->new("Day out of range: $day");
    }
    if ($hour < 0 || $hour > 23) {
        require Getdate::DateParseError;
        die Getdate::DateParseError->new("Hour out of range: $hour");
    }
    if ($minute < 0 || $minute > 59) {
        require Getdate::DateParseError;
        die Getdate::DateParseError->new("Minute out of range: $minute");
    }
    if ($second < 0 || $second > 59) {
        require Getdate::DateParseError;
        die Getdate::DateParseError->new("Second out of range: $second");
    }
    
    my $self = bless {
        year   => $year,
        month  => $month,
        day    => $day,
        hour   => $hour,
        minute => $minute,
        second => $second,
        tz     => $tz // 'local',
        _epoch => undef,
    }, $class;
    
    $self->_update_epoch;
    return $self;
}

sub now {
    my ($class, %params) = @_;
    
    my ($sec, $min, $hour, $mday, $mon, $year) = localtime(time);
    
    return $class->new(
        year   => $year + 1900,
        month  => $mon + 1,
        day    => $mday,
        hour   => $hour,
        minute => $min,
        second => $sec,
        tz     => $params{tz} // 'local',
    );
}

sub _update_epoch {
    my ($self) = @_;
    
    my $epoch;
    if ($self->{tz} eq 'UTC' || $self->{tz} eq 'GMT') {
        $epoch = timegm($self->{second}, $self->{minute}, $self->{hour}, 
                        $self->{day}, $self->{month} - 1, $self->{year} - 1900);
    } else {
        $epoch = timelocal($self->{second}, $self->{minute}, $self->{hour}, 
                          $self->{day}, $self->{month} - 1, $self->{year} - 1900);
    }
    $self->{_epoch} = $epoch;
}

sub epoch {
    my ($self) = @_;
    return $self->{_epoch};
}

sub from_epoch {
    my ($self_or_class, %params) = @_;
    my $class = ref($self_or_class) || $self_or_class;
    
    my $epoch = $params{epoch} // 0;
    my $tz = $params{tz} // 'local';
    
    my ($sec, $min, $hour, $mday, $mon, $year);
    if ($tz eq 'UTC' || $tz eq 'GMT') {
        ($sec, $min, $hour, $mday, $mon, $year) = gmtime($epoch);
    } else {
        ($sec, $min, $hour, $mday, $mon, $year) = localtime($epoch);
    }
    
    return $class->new(
        year   => $year + 1900,
        month  => $mon + 1,
        day    => $mday,
        hour   => $hour,
        minute => $min,
        second => $sec,
        tz     => $tz,
    );
}

sub year   { shift->{year} }
sub month  { shift->{month} }
sub day    { shift->{day} }
sub hour   { shift->{hour} }
sub minute { shift->{minute} }
sub second { shift->{second} }
sub tzinfo { shift->{tz} }

sub weekday {
    my ($self) = @_;
    
    my ($sec, $min, $hour, $mday, $mon, $year) = localtime($self->{_epoch});
    return $self->{tz} eq 'UTC' || $self->{tz} eq 'GMT' 
        ? (gmtime($self->{_epoch}))[6] 
        : (localtime($self->{_epoch}))[6];
}

sub ymd {
    my ($self, $sep) = @_;
    $sep //= '-';
    return sprintf("%04d%c%02d%c%02d", $self->{year}, $sep, $self->{month}, $sep, $self->{day});
}

sub hms {
    my ($self, $sep) = @_;
    $sep //= ':';
    return sprintf("%02d%c%02d%c%02d", $self->{hour}, $sep, $self->{minute}, $sep, $self->{second});
}

sub strftime {
    my ($self, $format) = @_;
    $format //= '%Y-%m-%d %H:%M:%S';
    
    my ($sec, $min, $hour, $mday, $mon, $year);
    if ($self->{tz} eq 'UTC' || $self->{tz} eq 'GMT') {
        ($sec, $min, $hour, $mday, $mon, $year) = gmtime($self->{_epoch});
    } else {
        ($sec, $min, $hour, $mday, $mon, $year) = localtime($self->{_epoch});
    }
    
    my %vars = (
        '%Y' => $year + 1900,
        '%m' => sprintf('%02d', $mon + 1),
        '%d' => sprintf('%02d', $mday),
        '%H' => sprintf('%02d', $hour),
        '%M' => sprintf('%02d', $min),
        '%S' => sprintf('%02d', $sec),
        '%y' => sprintf('%02d', ($year + 1900) % 100),
        '%a' => ['Sun','Mon','Tue','Wed','Thu','Fri','Sat']->[$self->weekday],
        '%A' => ['Sunday','Monday','Tuesday','Wednesday','Thursday','Friday','Saturday']->[$self->weekday],
        '%b' => ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']->[$mon],
        '%B' => ['January','February','March','April','May','June','July','August','September','October','November','December']->[$mon],
    );
    
    my $result = $format;
    for my $k (keys %vars) {
        $result =~ s/\Q$k\E/$vars{$k}/g;
    }
    return $result;
}

sub add {
    my ($self, $duration) = @_;
    
    my $epoch = $self->{_epoch};
    $epoch += $duration->{seconds} if $duration->{seconds};
    $epoch += ($duration->{days} // 0) * 86400;
    $epoch += ($duration->{hours} // 0) * 3600;
    $epoch += ($duration->{minutes} // 0) * 60;
    $epoch += ($duration->{weeks} // 0) * 604800;
    
    return $self->from_epoch(epoch => $epoch, tz => $self->{tz});
}

sub subtract {
    my ($self, $duration_or_datetime) = @_;
    
    if (ref($duration_or_datetime) eq 'Getdate::DateTime') {
        my $diff = $self->{_epoch} - $duration_or_datetime->{_epoch};
        require Getdate::DateInterval;
        return Getdate::DateInterval->new(seconds => $diff);
    } else {
        my $duration = $duration_or_datetime;
        my $epoch = $self->{_epoch};
        $epoch -= $duration->{seconds} if $duration->{seconds};
        $epoch -= ($duration->{days} // 0) * 86400;
        $epoch -= ($duration->{hours} // 0) * 3600;
        $epoch -= ($duration->{minutes} // 0) * 60;
        $epoch -= ($duration->{weeks} // 0) * 604800;
        
        return $self->from_epoch(epoch => $epoch, tz => $self->{tz});
    }
}

sub add_months {
    my ($self, $months) = @_;
    
    my $year = $self->{year};
    my $month = $self->{month} + $months;
    
    while ($month > 12) {
        $month -= 12;
        $year++;
    }
    while ($month < 1) {
        $month += 12;
        $year--;
    }
    
    my $day = $self->{day};
    my $max_day = _days_in_month($year, $month);
    $day = $max_day if $day > $max_day;
    
    return __PACKAGE__->new(
        year   => $year,
        month  => $month,
        day    => $day,
        hour   => $self->{hour},
        minute => $self->{minute},
        second => $self->{second},
        tz     => $self->{tz},
    );
}

sub _days_in_month {
    my ($year, $month) = @_;
    
    my @days = (31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31);
    
    if ($month == 2 && $year % 4 == 0 && ($year % 100 != 0 || $year % 400 == 0)) {
        return 29;
    }
    return $days[$month - 1];
}

sub clone {
    my ($self) = @_;
    return __PACKAGE__->new(
        year   => $self->{year},
        month  => $self->{month},
        day    => $self->{day},
        hour   => $self->{hour},
        minute => $self->{minute},
        second => $self->{second},
        tz     => $self->{tz},
    );
}

sub format {
    my ($self, $format) = @_;
    return $self->strftime($format // '%Y-%m-%d %H:%M:%S');
}

sub date {
    my ($self) = @_;
    return Getdate::DateTime->new(
        year   => $self->{year},
        month  => $self->{month},
        day    => $self->{day},
        hour   => 0,
        minute => 0,
        second => 0,
        tz     => $self->{tz},
    );
}

1;
