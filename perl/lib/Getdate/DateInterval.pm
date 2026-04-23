package Getdate::DateInterval;

use strict;
use warnings;

our $VERSION = '0.01';

sub new {
    my ($class, %params) = @_;
    
    return bless {
        years   => $params{years}   // 0,
        months  => $params{months}  // 0,
        days    => $params{days}    // 0,
        hours   => $params{hours}   // 0,
        minutes => $params{minutes} // 0,
        seconds => $params{seconds} // 0,
        weeks   => $params{weeks}   // 0,
    }, $class;
}

sub years   { shift->{years} }
sub months  { shift->{months} }
sub days    { shift->{days} }
sub hours   { shift->{hours} }
sub minutes { shift->{minutes} }
sub seconds { shift->{seconds} }
sub weeks   { shift->{weeks} }

sub in_seconds {
    my ($self) = @_;
    
    my $total = $self->{seconds};
    $total += ($self->{minutes} // 0) * 60;
    $total += ($self->{hours} // 0) * 3600;
    $total += ($self->{days} // 0) * 86400;
    $total += ($self->{weeks} // 0) * 604800;
    $total += ($self->{years} // 0) * 31536000;
    $total += ($self->{months} // 0) * 2592000;
    
    return $total;
}

sub in_days {
    my ($self) = @_;
    return int($self->in_seconds / 86400);
}

sub format {
    my ($self, $format) = @_;
    $format //= '%a days';
    
    my $result = $format;
    $result =~ s/%y/$self->{years}/g;
    $result =~ s/%m/$self->{months}/g;
    $result =~ s/%d/$self->{days}/g;
    $result =~ s/%h/$self->{hours}/g;
    $result =~ s/%i/$self->{minutes}/g;
    $result =~ s/%s/$self->{seconds}/g;
    
    my $in_days = $self->in_days;
    $result =~ s/%a/$in_days/g;
    
    my $sign = $self->in_seconds >= 0 ? '+' : '-';
    $result =~ s/%R/$sign/g;
    
    $sign = $self->in_seconds >= 0 ? '' : '-';
    $result =~ s/%r/$sign/g;
    
    return $result;
}

sub days {
    my ($self) = @_;
    return $self->in_days;
}

1;
