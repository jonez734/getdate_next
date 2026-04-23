package Getdate::Lexer;

use strict;
use warnings;

our $VERSION = '0.01';

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

{
    package Getdate::Lexer::Token;
    
    sub new {
        my ($class, $type, $value, $position) = @_;
        return bless {
            type     => $type,
            value    => $value,
            position => $position,
        }, $class;
    }
    
    sub type     { shift->{type} }
    sub value    { shift->{value} }
    sub position { shift->{position} }
    
    sub type_name {
        my ($self) = @_;
        my @names = qw(UNDEF NUMBER WORD MODIFIER TIME OFFSET ORDINAL DAY MONTH UNIT 
                        DATE_SEPARATOR TIME_SEPARATOR TIMEZONE COMMA UNIX AT EOF);
        return $names[$self->{type}] // 'UNKNOWN';
    }
}

our %MODIFIERS = map { $_ => 1 } qw(next last previous);
our %OFFSETS   = map { $_ => 1 } qw(ago from now until since);
our %UNITS     = map { $_ => 1 } qw(day days week weeks month months year years 
                                   hour hours minute minutes second seconds);
our %DAYS      = map { $_ => 1 } qw(monday tuesday wednesday thursday friday saturday sunday
                                    mon tue wed thu fri sat sun);
our %MONTHS    = map { $_ => 1 } qw(january february march april may june july august
                                    september october november december jan feb mar apr
                                    jun jul aug sep oct nov dec);
our %TIME_WORDS = map { $_ => 1 } qw(noon midday midnight night morning evening am pm a p of);
our %ORDINALS  = map { $_ => 1 } qw(first second third fourth fifth sixth seventh eighth 
                                    ninth tenth eleventh twelfth 1st 2nd 3rd 4th 5th 6th 
                                    7th 8th 9th 10th 11th 12th);

our %TIMEZONES = (
    est => 1, cst => 1, mst => 1, pst => 1,
    edt => 1, cdt => 1, mdt => 1, pdt => 1,
    gmt => 1, utc => 1, z => 1, bst => 1,
    cet => 1, cest => 1, jst => 1, aest => 1,
    aedt => 1, nzst => 1, nzdt => 1,
);

sub tokenize {
    my ($buf) = @_;
    
    return [] unless defined $buf && $buf ne '';
    
    $buf = lc($buf);
    $buf =~ s/^\s+|\s+$//g;
    
    my @tokens;
    my $pos = 0;
    my $len = length($buf);
    my $prev_type;
    
    while ($pos < $len) {
        if ($buf =~ /^\s/g) {
            $pos++;
            next;
        }
        
        my ($token, $new_pos) = _next_token($buf, $pos, $prev_type);
        if ($token) {
            push @tokens, $token;
            $prev_type = $token->type;
        }
        $pos = $new_pos;
    }
    
    push @tokens, Getdate::Lexer::Token->new(EOF, '', $pos);
    return \@tokens;
}

sub new {
    my ($class) = @_;
    return bless {}, $class;
}

sub _next_token {
    my ($buf, $pos, $prev_type) = @_;
    
    my $char = substr($buf, $pos, 1);
    
    if ($char =~ /^\d$/) {
        return _tokenize_number($buf, $pos, $prev_type);
    }
    if ($char =~ /^[a-zA-Z]$/) {
        return _tokenize_word($buf, $pos);
    }
    if ($char =~ /^[-+\/]$/) {
        return _tokenize_separator($buf, $pos, $prev_type);
    }
    if ($char eq ':') {
        $pos++;
        my $token = Getdate::Lexer::Token->new(TIME_SEPARATOR, ':', $pos - 1);
        return ($token, $pos);
    }
    if ($char eq ',') {
        $pos++;
        my $token = Getdate::Lexer::Token->new(COMMA, ',', $pos - 1);
        return ($token, $pos);
    }
    
    return (undef, $pos + 1);
}

sub _tokenize_number {
    my ($buf, $pos, $prev_type) = @_;
    
    my $start = $pos;
    while ($pos < length($buf) && substr($buf, $pos, 1) =~ /^\d$/) {
        $pos++;
    }
    
    my $value = substr($buf, $start, $pos - $start);
    
    if ($pos < length($buf)) {
        my $next_char = substr($buf, $pos, 1);
        
        if ($next_char =~ /^[stndrth]$/) {
            my $suffix = '';
            while ($pos < length($buf) && substr($buf, $pos, 1) =~ /^[stndrth]$/) {
                $suffix .= substr($buf, $pos, 1);
                $pos++;
            }
            $value .= $suffix;
            if (exists $ORDINALS{$value}) {
                my $token = Getdate::Lexer::Token->new(ORDINAL, $value, $start);
                return ($token, $pos);
            }
            my $token = Getdate::Lexer::Token->new(NUMBER, $value, $start);
            return ($token, $pos);
        }
        
        if ($next_char eq 'a' || $next_char eq 'p' || substr($buf, $pos) =~ /^am$/i || substr($buf, $pos) =~ /^pm$/i) {
            if (length($value) >= 3 && length($value) <= 4 && $value =~ /^\d+$/) {
                my $token = Getdate::Lexer::Token->new(NUMBER, $value, $start);
                return ($token, $pos);
            }
            my $ampm = '';
            while ($pos < length($buf) && substr($buf, $pos, 1) =~ /^[a-zA-Z]$/) {
                $ampm .= substr($buf, $pos, 1);
                $pos++;
            }
            $value .= $ampm;
            my $token = Getdate::Lexer::Token->new(TIME, $value, $start);
            return ($token, $pos);
        }
        
        if ($next_char eq ':') {
            my $time_val = $value;
            while ($pos < length($buf) && substr($buf, $pos, 1) =~ /^[\d:]$/) {
                $time_val .= substr($buf, $pos, 1);
                $pos++;
            }
            if ($pos < length($buf)) {
                my $c = substr($buf, $pos, 1);
                if ($c eq 'a' || $c eq 'p') {
                    my $ampm = '';
                    while ($pos < length($buf) && substr($buf, $pos, 1) =~ /^[a-zA-Z]$/) {
                        $ampm .= substr($buf, $pos, 1);
                        $pos++;
                    }
                    $time_val .= $ampm;
                }
            }
            my $token = Getdate::Lexer::Token->new(TIME, $time_val, $start);
            return ($token, $pos);
        }
    }
    
    if ($value eq '10' && length($value) == 2) {
        my $token = Getdate::Lexer::Token->new(NUMBER, $value, $start);
        return ($token, $pos);
    }
    
    if (length($value) == 10 && $value =~ /^\d{10}$/) {
        my $token = Getdate::Lexer::Token->new(UNIX, $value, $start);
        return ($token, $pos);
    }
    
    if ($value =~ /^\d{8}$/) {
        my $token = Getdate::Lexer::Token->new(NUMBER, $value, $start);
        return ($token, $pos);
    }
    
    my $token = Getdate::Lexer::Token->new(NUMBER, $value, $start);
    return ($token, $pos);
}

sub _tokenize_word {
    my ($buf, $pos) = @_;
    
    my $start = $pos;
    while ($pos < length($buf) && substr($buf, $pos, 1) =~ /^[a-zA-Z0-9]$/) {
        $pos++;
    }
    
    my $value = substr($buf, $start, $pos - $start);
    
    if (exists $MODIFIERS{$value}) {
        my $token = Getdate::Lexer::Token->new(MODIFIER, $value, $start);
        return ($token, $pos);
    }
    if (exists $DAYS{$value}) {
        my $token = Getdate::Lexer::Token->new(DAY, $value, $start);
        return ($token, $pos);
    }
    if (exists $MONTHS{$value}) {
        my $token = Getdate::Lexer::Token->new(MONTH, $value, $start);
        return ($token, $pos);
    }
    if (exists $TIME_WORDS{$value}) {
        my $token = Getdate::Lexer::Token->new(TIME, $value, $start);
        return ($token, $pos);
    }
    if (exists $UNITS{$value}) {
        my $token = Getdate::Lexer::Token->new(UNIT, $value, $start);
        return ($token, $pos);
    }
    if (exists $OFFSETS{$value}) {
        my $token = Getdate::Lexer::Token->new(OFFSET, $value, $start);
        return ($token, $pos);
    }
    if (exists $ORDINALS{$value}) {
        my $token = Getdate::Lexer::Token->new(ORDINAL, $value, $start);
        return ($token, $pos);
    }
    if (exists $TIMEZONES{$value}) {
        my $token = Getdate::Lexer::Token->new(TIMEZONE, $value, $start);
        return ($token, $pos);
    }
    if ($value eq 'at') {
        my $token = Getdate::Lexer::Token->new(AT, $value, $start);
        return ($token, $pos);
    }
    
    my $token = Getdate::Lexer::Token->new(WORD, $value, $start);
    return ($token, $pos);
}

sub _tokenize_separator {
    my ($buf, $pos, $prev_type) = @_;
    
    my $char = substr($buf, $pos, 1);
    $pos++;
    
    if (($char eq '+' || $char eq '-') && defined $prev_type && $prev_type == TIME) {
        my $tz_val = $char;
        while ($pos < length($buf) && (substr($buf, $pos, 1) =~ /^\d$/ || substr($buf, $pos, 1) eq ':')) {
            $tz_val .= substr($buf, $pos, 1);
            $pos++;
        }
        my $token = Getdate::Lexer::Token->new(TIMEZONE, $tz_val, $pos - length($tz_val));
        return ($token, $pos);
    }
    
    my $token = Getdate::Lexer::Token->new(DATE_SEPARATOR, $char, $pos - 1);
    return ($token, $pos);
}

1;
