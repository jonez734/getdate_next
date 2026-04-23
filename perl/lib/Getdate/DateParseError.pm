package Getdate::DateParseError;

use strict;
use warnings;

our $VERSION = '0.01';

sub new {
    my ($class, $message) = @_;
    $message //= 'Date parsing failed';
    return bless { message => $message }, $class;
}

sub message { shift->{message} }

sub string { shift->{message} }

1;
