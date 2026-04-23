package Getdate::Getdate;

use strict;
use warnings;

our $VERSION = '0.01';

use Getdate::Parser;
use Getdate::DateTime;
use Getdate::DateInterval;

sub getdate {
    my ($buf) = @_;
    
    return undef unless defined $buf && $buf ne '';
    
    $buf =~ s/^\s+|\s+$//g;
    return undef if $buf eq '';
    
    my $buf_lc = lc($buf);
    
    my %simple = (
        now => 0,
        today => 0,
        yesterday => -1,
        tomorrow => 1,
    );
    
    if (exists $simple{$buf_lc}) {
        return Getdate::DateTime->now->add({days => $simple{$buf_lc}});
    }
    
    if ($buf_lc =~ /^days?\s+until\s+/i) {
        my $date_expr = $buf;
        $date_expr =~ s/^days?\s+until\s+//i;
        my $target = getdate($date_expr);
        if ($target && ref($target) eq 'Getdate::DateTime') {
            my $now = Getdate::DateTime->now;
            my $diff = $target->{_epoch} - $now->{_epoch};
            return Getdate::DateInterval->new(seconds => $diff);
        }
        return undef;
    }
    
    if ($buf_lc =~ /^days?\s+since\s+/i) {
        my $date_expr = $buf;
        $date_expr =~ s/^days?\s+since\s+//i;
        my $target = getdate($date_expr);
        if ($target && ref($target) eq 'Getdate::DateTime') {
            my $now = Getdate::DateTime->now;
            my $diff = $now->{_epoch} - $target->{_epoch};
            return Getdate::DateInterval->new(seconds => $diff);
        }
        return undef;
    }
    
    return Getdate::Parser::getdate_with_lexer($buf_lc);
}

sub getdate_timestamp {
    my ($buf) = @_;
    
    my $result = getdate($buf);
    if (ref($result) eq 'Getdate::DateTime') {
        return $result->epoch;
    }
    return undef;
}

sub verify_valid_date_expression {
    my ($buf) = @_;
    
    return defined getdate($buf) ? 1 : 0;
}

1;

__END__

=head1 NAME

Getdate::Getdate - Parse natural language date expressions

=head1 SYNOPSIS

  use Getdate::Getdate;
  
  my $dt = Getdate::Getdate::getdate("next friday");
  print $dt->format("%Y-%m-%d %H:%M:%S");
  
  my $interval = Getdate::Getdate::getdate("days until 2nd wednesday april 2026");
  print $interval->format("%a days");
  
  my $ts = Getdate::Getdate::getdate_timestamp("next friday");
  
  if (Getdate::Getdate::verify_valid_date_expression("tomorrow")) {
      print "Valid date expression!\n";
  }

=head1 DESCRIPTION

Parse natural language date expressions into DateTime-like objects.
Returns timezone-aware datetime objects, or DateInterval for "days until/since" expressions.

=cut
