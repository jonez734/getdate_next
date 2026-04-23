package Getdate::Parser;

use strict;
use warnings;

our $VERSION = '0.01';

use Getdate::Lexer;
use Getdate::DateTime;
use Getdate::DateInterval;
use Getdate::DateParseError;
use Getdate::TimezoneData;

use constant {
    NUMBER        => 1,
    WORD          => 2,
    MODIFIER      => 3,
    TIME          => 4,
    OFFSET        => 5,
    ORDINAL       => 6,
    DAY           => 7,
    MONTH         => 8,
    UNIT          => 9,
    DATE_SEPARATOR => 10,
    TIME_SEPARATOR => 11,
    TIMEZONE      => 12,
    COMMA         => 13,
    UNIX          => 14,
    AT            => 15,
    EOF           => 16,
};

our %DAYS = (
    monday => 0, tuesday => 1, wednesday => 2, thursday => 3,
    friday => 4, saturday => 5, sunday => 6,
    mon => 0, tue => 1, wed => 2, thu => 3, fri => 4, sat => 5, sun => 6,
);

our %MONTHS = (
    january => 1, february => 2, march => 3, april => 4, may => 5, june => 6,
    july => 7, august => 8, september => 9, october => 10, november => 11, december => 12,
    jan => 1, feb => 2, mar => 3, apr => 4, jun => 6, jul => 7, aug => 8, sep => 9, 
    oct => 10, nov => 11, dec => 12,
);

our %ORDINALS = (
    first => 1, second => 2, third => 3, fourth => 4, fifth => 5, sixth => 6,
    seventh => 7, eighth => 8, ninth => 9, tenth => 10, eleventh => 11, twelfth => 12,
    '1st' => 1, '2nd' => 2, '3rd' => 3, '4th' => 4, '5th' => 5, '6th' => 6,
    '7th' => 7, '8th' => 8, '9th' => 9, '10th' => 10, '11th' => 11, '12th' => 12,
);

sub new {
    my ($class, $tokens) = @_;
    
    my $self = bless {
        tokens => $tokens,
        pos    => 0,
        now    => Getdate::DateTime->now,
    }, $class;
    
    return $self;
}

sub parse {
    my ($self) = @_;
    
    return undef if !$self->{tokens} || @{$self->{tokens}} == 0;
    return undef if $self->{tokens}[0]->type == EOF;
    
    my @parsers = (
        'parse_unix_timestamp',
        'parse_absolute_numeric',
        'parse_rfc822',
        'parse_rfc1123',
        'parse_rfc3339',
        'parse_full_date_time',
        'parse_us_datetime',
        'parse_international_date',
        'parse_iso8601',
        'parse_relative_with_time',
        'parse_day_at_time',
        'parse_ordinal_with_relative',
        'parse_relative_offset',
        'parse_relative_day',
        'parse_ordinal_day',
        'parse_relative_unit',
        'parse_days_until',
        'parse_days_since',
    );
    
    for my $parser (@parsers) {
        $self->{pos} = 0;
        my $result;
        eval {
            $result = $self->$parser();
        };
        if ($@) {
            warn "Exception in $parser: $@";
            next;
        }
        if (defined $result) {
            return $result;
        }
    }
    
    return undef;
}

sub peek {
    my ($self) = @_;
    return $self->{tokens}[$self->{pos}] // $self->{tokens}[-1];
}

sub advance {
    my ($self) = @_;
    return $self->{tokens}[$self->{pos}++];
}

sub reset {
    my ($self) = @_;
    $self->{pos} = 0;
}

sub reconstruct {
    my ($self) = @_;
    my $buf = '';
    for my $tok (@{$self->{tokens}}) {
        last if $tok->type == EOF;
        $buf .= $tok->value;
    }
    return $buf;
}

sub reconstruct_with_sep {
    my ($self) = @_;
    my $buf = '';
    my $prev_type;
    for my $tok (@{$self->{tokens}}) {
        last if $tok->type == EOF;
        if ($buf && $tok->type != DATE_SEPARATOR && $tok->type != TIME_SEPARATOR && $prev_type && 
            $prev_type != DATE_SEPARATOR && $prev_type != TIME_SEPARATOR) {
            $buf .= ' ';
        }
        $buf .= $tok->value;
        $prev_type = $tok->type;
    }
    return $buf;
}

sub parse_time {
    my ($self, $time_val) = @_;
    
    $time_val = lc($time_val);
    $time_val =~ s/^\s+|\s+$//g;
    
    my %special_times = (
        noon => [12, 0], midday => [12, 0], midnight => [0, 0], night => [21, 0],
    );
    
    if (exists $special_times{$time_val}) {
        return $special_times{$time_val};
    }
    
    if ($time_val =~ /^(\d{1,2}):(\d{2})(?::(\d{2}))?\s*(a|p|am|pm)?$/i) {
        my $hour = $1 + 0;
        my $minute = $2 + 0;
        my $ampm = $4;
        
        if ($ampm) {
            $ampm = lc($ampm);
            if (($ampm eq 'p' || $ampm eq 'pm') && $hour != 12) {
                $hour += 12;
            } elsif (($ampm eq 'a' || $ampm eq 'am') && $hour == 12) {
                $hour = 0;
            }
        }
        
        if ($hour >= 0 && $hour <= 23 && $minute >= 0 && $minute <= 59) {
            return [$hour, $minute];
        }
    }
    
    if ($time_val =~ /^(\d{1,2})\s*(a|p|am|pm)?$/i) {
        my $hour = $1 + 0;
        my $ampm = $2;
        
        if ($ampm) {
            $ampm = lc($ampm);
            if (($ampm eq 'p' || $ampm eq 'pm') && $hour != 12) {
                $hour += 12;
            } elsif (($ampm eq 'a' || $ampm eq 'am') && $hour == 12) {
                $hour = 0;
            }
        }
        
        if ($hour >= 0 && $hour <= 23) {
            return [$hour, 0];
        }
    }
    
    return undef;
}

sub parse_unix_timestamp {
    my ($self) = @_;
    
    my $tok = $self->peek;
    return undef if $tok->type != UNIX;
    
    $self->advance;
    my $ts = $tok->value + 0;
    
    return Getdate::DateTime->from_epoch(epoch => $ts);
}

sub parse_absolute_numeric {
    my ($self) = @_;
    
    return undef if $self->{pos} != 0;
    
    my $buf = $self->{tokens}[0] ? $self->{tokens}[0]->value : '';
    return undef if length($buf) != 12 || $buf !~ /^\d+$/;
    
    my $year  = substr($buf, 0, 4) + 0;
    my $month = substr($buf, 4, 2) + 0;
    my $day   = substr($buf, 6, 2) + 0;
    my $hour  = substr($buf, 8, 2) + 0;
    my $min   = substr($buf, 10, 2) + 0;
    
    return Getdate::DateTime->new(
        year   => $year,
        month  => $month,
        day    => $day,
        hour   => $hour,
        minute => $min,
        second => 0,
    );
}

sub parse_iso8601 {
    my ($self) = @_;
    
    my $buf = $self->reconstruct;
    return undef if index($buf, '-') < 0 && index($buf, 'T') < 0;
    
    if ($buf =~ /^(\d{4})-(\d{2})-(\d{2})[T ](\d{2}):(\d{2}):(\d{2})(?:\.(\d+))?(Z|[+-]\d{2}:?\d{2})?$/i) {
        my $year = $1 + 0;
        my $month = $2 + 0;
        my $day = $3 + 0;
        my $hour = $4 + 0;
        my $minute = $5 + 0;
        my $second = $6 + 0;
        my $tz = $8;
        
        my $tz_str = 'local';
        if ($tz && uc($tz) eq 'Z') {
            $tz_str = 'UTC';
        } elsif ($tz) {
            my $sign = substr($tz, 0, 1) eq '+' ? 1 : -1;
            my $tz_hour = substr($tz, 1, 2) + 0;
            my $tz_min = substr($tz, 3) // '';
            $tz_min =~ s/://g;
            $tz_min = ($tz_min // 0) + 0;
            $tz_str = sprintf("%s%02d%02d", $sign > 0 ? '+' : '-', $tz_hour, $tz_min);
        }
        
        return Getdate::DateTime->new(
            year   => $year,
            month  => $month,
            day    => $day,
            hour   => $hour,
            minute => $minute,
            second => $second,
            tz     => $tz_str,
        );
    }
    
    if ($buf =~ /^(\d{4})-(\d{2})-(\d{2})$/) {
        my $year = $1 + 0;
        my $month = $2 + 0;
        my $day = $3 + 0;
        
        return Getdate::DateTime->new(
            year   => $year,
            month  => $month,
            day    => $day,
        );
    }
    
    return undef;
}

sub parse_us_datetime {
    my ($self) = @_;
    
    my $has_sep = 0;
    for my $tok (@{$self->{tokens}}) {
        if ($tok->type == DATE_SEPARATOR) {
            $has_sep = 1;
            last;
        }
    }
    return undef unless $has_sep;
    
    my $buf = $self->reconstruct_with_sep;
    
    if ($buf =~ /^(\d{1,2})\/(\d{1,2})\/(\d{2,4})(?:\s+(\d{1,2}):(\d{2})(?::(\d{2}))?\s*(a|p|am|pm)?)?$/i) {
        my $month = $1 + 0;
        my $day = $2 + 0;
        my $year_str = $3;
        
        my $year;
        if (length($year_str) == 2) {
            $year = 2000 + $year_str;
            $year += 100 if $year < 1970;
        } else {
            $year = $year_str + 0;
        }
        
        my ($hour, $minute, $second) = (0, 0, 0);
        
        if ($4) {
            $hour = $4 + 0;
            $minute = $5 + 0;
            $second = $6 ? $6 + 0 : 0;
            my $ampm = $7;
            if ($ampm) {
                $ampm = lc($ampm);
                if (($ampm eq 'p' || $ampm eq 'pm') && $hour != 12) {
                    $hour += 12;
                } elsif (($ampm eq 'a' || $ampm eq 'am') && $hour == 12) {
                    $hour = 0;
                }
            }
        }
        
        return Getdate::DateTime->new(
            year   => $year,
            month  => $month,
            day    => $day,
            hour   => $hour,
            minute => $minute,
            second => $second,
        );
    }
    
    return undef;
}

sub parse_relative_with_time {
    my ($self) = @_;
    
    my %simple_relative = (today => 0, yesterday => -1, tomorrow => 1);
    
    my $saved_pos = $self->{pos};
    my $tok1 = $self->peek;
    
    if ($tok1->type == WORD && exists $simple_relative{$tok1->value}) {
        $self->advance;
        my $day_offset = $simple_relative{$tok1->value};
        
        my $next_tok = $self->peek;
        if ($next_tok->type == TIME) {
            $self->advance;
            my $time_parsed = $self->parse_time($next_tok->value);
            if ($time_parsed) {
                my ($hour, $minute) = @$time_parsed;
                my $target_dt = $self->{now}->add({days => $day_offset});
                return Getdate::DateTime->new(
                    year   => $target_dt->year,
                    month  => $target_dt->month,
                    day    => $target_dt->day,
                    hour   => $hour,
                    minute => $minute,
                    second => 0,
                );
            }
        }
    }
    
    $self->{pos} = $saved_pos;
    
    $tok1 = $self->peek;
    if ($tok1->type == MODIFIER) {
        $self->advance;
        my $modifier = $tok1->value;
        
        my $day_tok = $self->peek;
        if ($day_tok->type == DAY) {
            $self->advance;
            my $target_day = $DAYS{$day_tok->value};
            
            my $time_tok = $self->peek;
            if ($time_tok->type == TIME) {
                $self->advance;
                my $time_parsed = $self->parse_time($time_tok->value);
                if ($time_parsed) {
                    my ($hour, $minute) = @$time_parsed;
                    
                    my $days_ahead = $target_day - $self->{now}->weekday;
                    if ($modifier eq 'next') {
                        $days_ahead += 7 if $days_ahead <= 0;
                    } else {
                        $days_ahead -= 7 if $days_ahead >= 0;
                    }
                    
                    my $target_dt = $self->{now}->add({days => $days_ahead});
                    return Getdate::DateTime->new(
                        year   => $target_dt->year,
                        month  => $target_dt->month,
                        day    => $target_dt->day,
                        hour   => $hour,
                        minute => $minute,
                        second => 0,
                    );
                }
            }
        }
    }
    
    $self->{pos} = $saved_pos;
    
    $tok1 = $self->peek;
    if ($tok1->type == DAY) {
        $self->advance;
        my $target_day = $DAYS{$tok1->value};
        
        my $time_tok = $self->peek;
        if ($time_tok->type == TIME) {
            $self->advance;
            my $time_parsed = $self->parse_time($time_tok->value);
            if ($time_parsed) {
                my ($hour, $minute) = @$time_parsed;
                
                my $days_ahead = $target_day - $self->{now}->weekday;
                $days_ahead += 7 if $days_ahead <= 0;
                
                my $target_dt = $self->{now}->add({days => $days_ahead});
                return Getdate::DateTime->new(
                    year   => $target_dt->year,
                    month  => $target_dt->month,
                    day    => $target_dt->day,
                    hour   => $hour,
                    minute => $minute,
                    second => 0,
                );
            }
        }
    }
    
    $self->{pos} = $saved_pos;
    return undef;
}

sub parse_relative_offset {
    my ($self) = @_;
    
    my $buf = $self->reconstruct_with_sep;
    
    if ($buf =~ /^([+-]?)(\d+)\s+(days?|weeks?|months?|hours?|minutes?|seconds?)\s*(ago|from now)?$/i) {
        my $sign_str = $1 // '';
        my $amount = $2 + 0;
        my $unit = $3;
        my $direction = $4 // '';
        
        my $sign = ($sign_str eq '-' || $direction eq 'ago') ? -1 : 1;
        $amount *= $sign;
        
        if ($unit =~ /^day/i) {
            return $self->{now}->add({days => $amount});
        } elsif ($unit =~ /^week/i) {
            return $self->{now}->add({weeks => $amount});
        } elsif ($unit =~ /^month/i) {
            return $self->{now}->add_months($amount);
        } elsif ($unit =~ /^hour/i) {
            return $self->{now}->add({hours => $amount});
        } elsif ($unit =~ /^minute/i) {
            return $self->{now}->add({minutes => $amount});
        } elsif ($unit =~ /^second/i) {
            return $self->{now}->add({seconds => $amount});
        }
    }
    
    return undef;
}

sub parse_relative_day {
    my ($self) = @_;
    
    my $saved_pos = $self->{pos};
    my $buf = $self->reconstruct_with_sep;
    
    if ($buf =~ /^(next|last|previous)\s+(monday|tuesday|wednesday|thursday|friday|saturday|sunday|mon|tue|wed|thu|fri|sat|sun)$/i) {
        my $direction = lc($1);
        my $day_name = lc($2);
        my $target_day = $DAYS{$day_name};
        
        my $days_ahead = $target_day - $self->{now}->weekday;
        if ($direction eq 'next') {
            $days_ahead += 7 if $days_ahead <= 0;
        } else {
            $days_ahead -= 7 if $days_ahead >= 0;
        }
        
        return $self->{now}->add({days => $days_ahead});
    }
    
    if (exists $DAYS{$buf}) {
        my $target_day = $DAYS{$buf};
        my $days_ahead = $target_day - $self->{now}->weekday;
        $days_ahead += 7 if $days_ahead <= 0;
        return $self->{now}->add({days => $days_ahead});
    }
    
    $self->{pos} = $saved_pos;
    return undef;
}

sub parse_ordinal_day {
    my ($self) = @_;
    
    my $saved_pos = $self->{pos};
    my $buf = $self->reconstruct_with_sep;
    
    if ($buf =~ /^(\d+(?:st|nd|rd|th)?|first|second|third|fourth|fifth)\s+(monday|tuesday|wednesday|thursday|friday|saturday|sunday|mon|tue|wed|thu|fri|sat|sun)\s+(?:of\s+)?(?:(january|february|march|april|may|june|july|august|september|october|november|december|jan|feb|mar|apr|jun|jul|aug|sep|oct|nov|dec)\s*)?(\d{4})?$/i) {
        my $ordinal_str = lc($1);
        my $day_name = lc($2);
        my $month_str = lc($3 // '');
        my $year_str = $4 // '';
        
        my $ordinal = $ORDINALS{$ordinal_str} // ($ordinal_str =~ /^\d+/ ? $ordinal_str + 0 : 1);
        my $target_day = $DAYS{$day_name};
        
        my $month = $month_str ? $MONTHS{$month_str} : $self->{now}->month;
        my $year = $year_str ? $year_str + 0 : $self->{now}->year;
        
        my $result;
        my $count = 0;
        for my $d (1 .. 31) {
            my $dt;
            eval { $dt = Getdate::DateTime->new(year => $year, month => $month, day => $d); };
            next if $@;
            
            if ($dt->weekday == $target_day) {
                $count++;
                if ($count == $ordinal) {
                    $result = Getdate::DateTime->new(
                        year   => $year,
                        month  => $month,
                        day    => $d,
                        hour   => $self->{now}->hour,
                        minute => $self->{now}->minute,
                        second => $self->{now}->second,
                    );
                    last;
                }
            }
        }
        
        return $result if $result;
        die Getdate::DateParseError->new("No $ordinal_str $day_name in $month/$year");
    }
    
    if ($buf =~ /^final\s+(monday|tuesday|wednesday|thursday|friday|saturday|sunday|mon|tue|wed|thu|fri|sat|sun)\s+(?:of\s+)?(?:(january|february|march|april|may|june|july|august|september|october|november|december|jan|feb|mar|apr|jun|jul|aug|sep|oct|nov|dec)\s*)?(\d{4})?$/i) {
        my $day_name = lc($1);
        my $month_str = lc($2 // '');
        my $year_str = $3 // '';
        
        my $target_day = $DAYS{$day_name};
        my $month = $month_str ? $MONTHS{$month_str} : $self->{now}->month;
        my $year = $year_str ? $year_str + 0 : $self->{now}->year;
        
        my $last_occurrence;
        for my $d (reverse 1 .. 31) {
            my $dt;
            eval { $dt = Getdate::DateTime->new(year => $year, month => $month, day => $d); };
            next if $@;
            
            if ($dt->weekday == $target_day) {
                $last_occurrence = $d;
                last;
            }
        }
        
        if ($last_occurrence) {
            return Getdate::DateTime->new(
                year   => $year,
                month  => $month,
                day    => $last_occurrence,
                hour   => $self->{now}->hour,
                minute => $self->{now}->minute,
                second => $self->{now}->second,
            );
        }
        
        die Getdate::DateParseError->new("No $day_name in $month/$year");
    }
    
    $self->{pos} = $saved_pos;
    return undef;
}

sub parse_relative_unit {
    my ($self) = @_;
    
    my $buf = $self->reconstruct_with_sep;
    
    my %simple = (today => 0, yesterday => -1, tomorrow => 1, now => 0);
    
    if (exists $simple{$buf}) {
        return $self->{now}->add({days => $simple{$buf}});
    }
    
    if ($buf =~ /^(next|last|previous)\s+(week|month|year)$/i) {
        my $direction = lc($1);
        my $unit = lc($2);
        
        if ($unit eq 'week') {
            my $days = $direction eq 'next' ? 7 : -7;
            return $self->{now}->add({days => $days});
        } elsif ($unit eq 'month') {
            return $self->{now}->add_months($direction eq 'next' ? 1 : -1);
        } elsif ($unit eq 'year') {
            my $new_year = $self->{now}->year + ($direction eq 'next' ? 1 : -1);
            return Getdate::DateTime->new(
                year   => $new_year,
                month  => $self->{now}->month,
                day    => $self->{now}->day,
                hour   => $self->{now}->hour,
                minute => $self->{now}->minute,
                second => $self->{now}->second,
            );
        }
    }
    
    return undef;
}

sub parse_days_until {
    my ($self) = @_;
    
    my $buf = $self->reconstruct_with_sep;
    
    if ($buf =~ /^days?\s+until\s+(.+)$/i) {
        my $date_expr = $1;
        
        my $tokens = Getdate::Lexer::tokenize($date_expr);
        
        my $parser = Getdate::Parser->new($tokens);
        my $target_date = $parser->parse;
        
        if ($target_date) {
            my $diff = $target_date->{_epoch} - $self->{now}->{_epoch};
            return Getdate::DateInterval->new(seconds => $diff);
        }
    }
    
    return undef;
}

sub parse_days_since {
    my ($self) = @_;
    
    my $buf = $self->reconstruct_with_sep;
    
    if ($buf =~ /^days?\s+since\s+(.+)$/i) {
        my $date_expr = $1;
        
        my $tokens = Getdate::Lexer::tokenize($date_expr);
        
        my $parser = Getdate::Parser->new($tokens);
        my $target_date = $parser->parse;
        
        if ($target_date) {
            my $diff = $self->{now}->{_epoch} - $target_date->{_epoch};
            return Getdate::DateInterval->new(seconds => $diff);
        }
    }
    
    return undef;
}

sub parse_rfc822 {
    my ($self) = @_;
    
    my $buf = $self->reconstruct;
    
    if ($buf =~ /^([a-z]{3})\s+([a-z]{3})\s+(\d{1,2})\s+(\d{1,2}):(\d{2}):(\d{2})\s+(am|pm)\s+([a-z]{3})\s+(\d{4})$/i) {
        my $month_str = lc($2);
        my $day = $3 + 0;
        my $hour = $4 + 0;
        my $minute = $5 + 0;
        my $second = $6 + 0;
        my $ampm = lc($7);
        my $tz_abbr = lc($8);
        my $year = $9 + 0;
        
        if ($ampm eq 'pm' && $hour != 12) {
            $hour += 12;
        } elsif ($ampm eq 'am' && $hour == 12) {
            $hour = 0;
        }
        
        my $month = $MONTHS{$month_str};
        return undef unless $month;
        
        my $tz = Getdate::TimezoneData::get_timezone($tz_abbr) // 'UTC';
        
        return Getdate::DateTime->new(
            year   => $year,
            month  => $month,
            day    => $day,
            hour   => $hour,
            minute => $minute,
            second => $second,
            tz     => $tz,
        );
    }
    
    return undef;
}

sub parse_rfc1123 {
    my ($self) = @_;
    
    my $buf = $self->reconstruct;
    $buf =~ s/,//g;
    
    if ($buf =~ /^([a-z]{3})\s+(\d{1,2})\s+([a-z]{3})\s+(\d{4})\s+(\d{1,2}):(\d{2}):(\d{2})\s+([a-z]{3,4})$/i) {
        my $day = $2 + 0;
        my $month_str = lc($3);
        my $year = $4 + 0;
        my $hour = $5 + 0;
        my $minute = $6 + 0;
        my $second = $7 + 0;
        my $tz_abbr = lc($8);
        
        my $month = $MONTHS{$month_str};
        return undef unless $month;
        
        my $tz = Getdate::TimezoneData::get_timezone($tz_abbr) // 'UTC';
        
        return Getdate::DateTime->new(
            year   => $year,
            month  => $month,
            day    => $day,
            hour   => $hour,
            minute => $minute,
            second => $second,
            tz     => $tz,
        );
    }
    
    return undef;
}

sub parse_rfc3339 {
    my ($self) = @_;
    
    my $buf = $self->reconstruct;
    
    if ($buf =~ /^(\d{4})-(\d{2})-(\d{2})\s+(\d{2}):(\d{2}):(\d{2})([+-]\d{2}:\d{2}|Z)$/) {
        my $year = $1 + 0;
        my $month = $2 + 0;
        my $day = $3 + 0;
        my $hour = $4 + 0;
        my $minute = $5 + 0;
        my $second = $6 + 0;
        my $tz = $7;
        
        my $tz_str = 'local';
        if ($tz eq 'Z' || $tz eq 'z') {
            $tz_str = 'UTC';
        } else {
            $tz_str = $tz;
        }
        
        return Getdate::DateTime->new(
            year   => $year,
            month  => $month,
            day    => $day,
            hour   => $hour,
            minute => $minute,
            second => $second,
            tz     => $tz_str,
        );
    }
    
    return undef;
}

sub parse_full_date_time {
    my ($self) = @_;
    
    my $buf = $self->reconstruct;
    
    if ($buf =~ /^([a-z]+),\s+([a-z]+)\s+(\d{1,2}),\s+(\d{4})\s+(\d{1,2}):(\d{2})\s*(am|pm)?$/i) {
        my $dow = lc($1);
        my $month_str = lc($2);
        my $day = $3 + 0;
        my $year = $4 + 0;
        my $hour = $5 + 0;
        my $minute = $6 + 0;
        my $ampm = $7 ? lc($7) : '';
        
        if ($ampm eq 'pm' && $hour != 12) {
            $hour += 12;
        } elsif ($ampm eq 'am' && $hour == 12) {
            $hour = 0;
        }
        
        my $month = $MONTHS{$month_str};
        return undef unless $month;
        
        return Getdate::DateTime->new(
            year   => $year,
            month  => $month,
            day    => $day,
            hour   => $hour,
            minute => $minute,
            second => 0,
        );
    }
    
    return undef;
}

sub parse_international_date {
    my ($self) = @_;
    
    my $buf = $self->reconstruct_with_sep;
    
    if ($buf =~ /^(\d{1,2})[-\/](\d{1,2})[-\/](\d{4})$/) {
        my $day = $1 + 0;
        my $month = $2 + 0;
        my $year = $3 + 0;
        
        return Getdate::DateTime->new(
            year   => $year,
            month  => $month,
            day    => $day,
        );
    }
    
    if ($buf =~ /^(\d{1,2})-([a-z]{3})-(\d{4})$/i) {
        my $day = $1 + 0;
        my $month_str = lc($2);
        my $year = $3 + 0;
        
        my $month = $MONTHS{$month_str};
        return undef unless $month;
        
        return Getdate::DateTime->new(
            year   => $year,
            month  => $month,
            day    => $day,
        );
    }
    
    return undef;
}

sub parse_day_at_time {
    my ($self) = @_;
    
    my $saved_pos = $self->{pos};
    my $tok1 = $self->peek;
    
    if ($tok1->type == DAY) {
        $self->advance;
        my $day_name = $tok1->value;
        
        my $at_tok = $self->peek;
        if ($at_tok->type == AT) {
            $self->advance;
            my $time_tok = $self->peek;
            if ($time_tok->type == TIME) {
                $self->advance;
                my $time_parsed = $self->parse_time($time_tok->value);
                if ($time_parsed) {
                    my ($hour, $minute) = @$time_parsed;
                    my $target_day = $DAYS{$day_name};
                    
                    my $days_ahead = $target_day - $self->{now}->weekday;
                    $days_ahead += 7 if $days_ahead <= 0;
                    
                    my $target_dt = $self->{now}->add({days => $days_ahead});
                    return Getdate::DateTime->new(
                        year   => $target_dt->year,
                        month  => $target_dt->month,
                        day    => $target_dt->day,
                        hour   => $hour,
                        minute => $minute,
                        second => 0,
                    );
                }
            }
        }
    }
    
    $self->{pos} = $saved_pos;
    return undef;
}

sub parse_ordinal_with_relative {
    my ($self) = @_;
    
    return undef;
}

sub getdate_with_lexer {
    my ($buf) = @_;
    
    my $tokens = Getdate::Lexer::tokenize($buf);
    
    my $parser = Getdate::Parser->new($tokens);
    return $parser->parse;
}

1;
