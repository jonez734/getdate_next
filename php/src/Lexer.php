<?php

declare(strict_types=1);

namespace GetdateNext;

use UnitEnum;

enum TokenType: string
{
    case NUMBER = 'NUMBER';
    case WORD = 'WORD';
    case MODIFIER = 'MODIFIER';
    case TIME = 'TIME';
    case OFFSET = 'OFFSET';
    case ORDINAL = 'ORDINAL';
    case DAY = 'DAY';
    case MONTH = 'MONTH';
    case UNIT = 'UNIT';
    case DATE_SEPARATOR = 'DATE_SEPARATOR';
    case TIME_SEPARATOR = 'TIME_SEPARATOR';
    case TIMEZONE = 'TIMEZONE';
    case COMMA = 'COMMA';
    case UNIX = 'UNIX';
    case AT = 'AT';
    case EOF = 'EOF';
}

class Token
{
    public function __construct(
        public readonly TokenType $type,
        public readonly string $value,
        public readonly int $position,
    ) {
    }
}

class Lexer
{
    private const MODIFIERS = ['next', 'last', 'previous'];
    private const OFFSETS = ['ago', 'from', 'now', 'until', 'since'];
    private const UNITS = ['day', 'days', 'week', 'weeks', 'month', 'months', 'year', 'years', 'hour', 'hours', 'minute', 'minutes', 'second', 'seconds'];
    private const DAYS = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday', 'mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun'];
    private const MONTHS = ['january', 'february', 'march', 'april', 'may', 'june', 'july', 'august', 'september', 'october', 'november', 'december', 'jan', 'feb', 'mar', 'apr', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec'];
    private const TIME_WORDS = ['noon', 'midday', 'midnight', 'night', 'morning', 'evening', 'am', 'pm', 'a', 'p', 'of'];
    private const ORDINALS = ['first', 'second', 'third', 'fourth', 'fifth', 'sixth', 'seventh', 'eighth', 'ninth', 'tenth', 'eleventh', 'twelfth', '1st', '2nd', '3rd', '4th', '5th', '6th', '7th', '8th', '9th', '10th', '11th', '12th'];
    private const TIMEZONES = ['est', 'cst', 'mst', 'pst', 'edt', 'cdt', 'mdt', 'pdt', 'gmt', 'utc', 'z', 'bst', 'cet', 'cest', 'jst', 'aest', 'aedt', 'nzst', 'nzdt'];

    private string $buf;
    private int $pos = 0;
    private array $tokens = [];
    private ?TokenType $prevTokenType = null;

    public function tokenize(string $buf): array
    {
        $this->buf = strtolower(trim($buf));
        $this->pos = 0;
        $this->tokens = [];
        $this->prevTokenType = null;

        while ($this->pos < strlen($this->buf)) {
            $this->skipWhitespace();
            if ($this->pos >= strlen($this->buf)) {
                break;
            }

            $token = $this->nextToken();
            if ($token !== null) {
                $this->tokens[] = $token;
                $this->prevTokenType = $token->type;
            }
        }

        $this->tokens[] = new Token(TokenType::EOF, '', $this->pos);
        return $this->tokens;
    }

    private function skipWhitespace(): void
    {
        while ($this->pos < strlen($this->buf) && ctype_space($this->buf[$this->pos])) {
            $this->pos++;
        }
    }

    private function nextToken(): ?Token
    {
        if ($this->pos >= strlen($this->buf)) {
            return null;
        }

        $char = $this->buf[$this->pos];

        if (ctype_digit($char)) {
            return $this->tokenizeNumber();
        }
        if (ctype_alpha($char)) {
            $start = $this->pos;
            // Check for ISO 8601 T separator
            if (strtolower($char) === 't' && $this->pos + 1 < strlen($this->buf) && ctype_digit($this->buf[$this->pos + 1])) {
                $this->pos++;
                return new Token(TokenType::TIME_SEPARATOR, 'T', $start);
            }
            return $this->tokenizeWord();
        }
        if (in_array($char, ['-', '+', '/'], true)) {
            return $this->tokenizeSeparator();
        }
        if ($char === ':') {
            return $this->tokenizeTimeSeparator();
        }
        if ($char === ',') {
            return $this->tokenizeComma();
        }

        $this->pos++;
        return null;
    }

    private function tokenizeNumber(): Token
    {
        $start = $this->pos;
        while ($this->pos < strlen($this->buf) && ctype_digit($this->buf[$this->pos])) {
            $this->pos++;
        }

        $value = substr($this->buf, $start, $this->pos - $start);

        if ($this->pos < strlen($this->buf) && in_array($this->buf[$this->pos], ['s', 'n', 'd', 'r', 'h'], true)) {
            $suffix = '';
            while ($this->pos < strlen($this->buf) && in_array($this->buf[$this->pos], ['s', 't', 'n', 'd', 'r', 't', 'h'], true)) {
                $suffix .= $this->buf[$this->pos];
                $this->pos++;
            }
            $value = $value . $suffix;
            if (in_array($value, self::ORDINALS, true)) {
                return new Token(TokenType::ORDINAL, $value, $start);
            }
            return new Token(TokenType::NUMBER, $value, $start);
        }

        if ($this->pos < strlen($this->buf)) {
            $nextChar = strtolower($this->buf[$this->pos]);
            if (in_array($nextChar, ['a', 'p'], true) || str_starts_with(substr($this->buf, $this->pos), 'am') || str_starts_with(substr($this->buf, $this->pos), 'pm')) {
                $ampm = '';
                while ($this->pos < strlen($this->buf) && ctype_alpha($this->buf[$this->pos])) {
                    $ampm .= $this->buf[$this->pos];
                    $this->pos++;
                }
                return new Token(TokenType::TIME, $value . $ampm, $start);
            }

            if ($nextChar === ':') {
                $timeVal = $value;
                while ($this->pos < strlen($this->buf) && (ctype_digit($this->buf[$this->pos]) || $this->buf[$this->pos] === ':')) {
                    $timeVal .= $this->buf[$this->pos];
                    $this->pos++;
                }
                if ($this->pos < strlen($this->buf) && in_array(strtolower($this->buf[$this->pos]), ['a', 'p'], true)) {
                    $ampm = '';
                    while ($this->pos < strlen($this->buf) && ctype_alpha($this->buf[$this->pos])) {
                        $ampm .= $this->buf[$this->pos];
                        $this->pos++;
                    }
                    return new Token(TokenType::TIME, $timeVal . $ampm, $start);
                }
                return new Token(TokenType::TIME, $timeVal, $start);
            }
        }

        if (strlen($value) === 10 && ctype_digit($value)) {
            return new Token(TokenType::UNIX, $value, $start);
        }

        return new Token(TokenType::NUMBER, $value, $start);
    }

    private function tokenizeWord(): Token
    {
        $start = $this->pos;
        while ($this->pos < strlen($this->buf) && ctype_alnum($this->buf[$this->pos])) {
            $this->pos++;
        }

        $value = substr($this->buf, $start, $this->pos - $start);

        if (in_array($value, self::MODIFIERS, true)) {
            return new Token(TokenType::MODIFIER, $value, $start);
        }
        if (in_array($value, self::DAYS, true)) {
            return new Token(TokenType::DAY, $value, $start);
        }
        if (in_array($value, self::MONTHS, true)) {
            return new Token(TokenType::MONTH, $value, $start);
        }
        if (in_array($value, self::TIME_WORDS, true)) {
            return new Token(TokenType::TIME, $value, $start);
        }
        if (in_array($value, self::UNITS, true)) {
            return new Token(TokenType::UNIT, $value, $start);
        }
        if (in_array($value, self::OFFSETS, true)) {
            return new Token(TokenType::OFFSET, $value, $start);
        }
        if (in_array($value, self::ORDINALS, true)) {
            return new Token(TokenType::ORDINAL, $value, $start);
        }
        if (in_array($value, self::TIMEZONES, true)) {
            return new Token(TokenType::TIMEZONE, $value, $start);
        }
        if ($value === 'at') {
            return new Token(TokenType::AT, $value, $start);
        }

        return new Token(TokenType::WORD, $value, $start);
    }

    private function tokenizeSeparator(): Token
    {
        $char = $this->buf[$this->pos];
        $start = $this->pos;
        $this->pos++;

        if (in_array($char, ['+', '-'], true) && $this->prevTokenType === TokenType::TIME) {
            $tzVal = $char;
            while ($this->pos < strlen($this->buf) && (ctype_digit($this->buf[$this->pos]) || $this->buf[$this->pos] === ':')) {
                $tzVal .= $this->buf[$this->pos];
                $this->pos++;
            }
            return new Token(TokenType::TIMEZONE, $tzVal, $start);
        }

        return new Token(TokenType::DATE_SEPARATOR, $char, $start);
    }

    private function tokenizeTimeSeparator(): Token
    {
        $char = $this->buf[$this->pos];
        $this->pos++;
        return new Token(TokenType::TIME_SEPARATOR, $char, $this->pos - 1);
    }

    private function tokenizeComma(): Token
    {
        $char = $this->buf[$this->pos];
        $this->pos++;
        return new Token(TokenType::COMMA, $char, $this->pos - 1);
    }
}