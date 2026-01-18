# mathexlab/language/tokenizer.py

from dataclasses import dataclass
from typing import List


@dataclass
class Token:
    type: str
    value: str
    line: int = 0


# MATLAB keywords (lowercase compare)
KEYWORDS = {
    'if', 'elseif', 'else', 'end', 'for', 'while', 'break', 'continue',
    'global', 'switch', 'case', 'otherwise', 'try', 'catch',
    'function', 'return',
    'classdef', 'properties', 'methods', 'events'
}


class Tokenizer:
    """
    MATLAB-style lexical scanner.
    """
    def __init__(self, text: str):
        self.text = text
        self.pos = 0
        self.line = 1

    def tokenize(self) -> List[Token]:
        tokens: List[Token] = []
        # [FIX] Track if we just skipped space to distinguish '1 -5' from '1-5'
        space_skipped = True 

        while self.pos < len(self.text):
            ch = self.text[self.pos]

            # whitespace / newline
            if ch.isspace():
                if ch == '\n':
                    tokens.append(Token('NEWLINE', '\n', self.line))
                    self.line += 1
                self.pos += 1
                space_skipped = True
                continue

            # comment %
            if ch == '%':
                self._skip_comment()
                space_skipped = True
                continue

            # continuation ...
            if ch == '.' and self._peek(1) == '.' and self._peek(2) == '.':
                self._skip_line_continuation()
                space_skipped = True
                continue
            
            # -----------------------------------------------------------
            # [FIX] Signed Numbers (e.g. -5 inside [1 -5])
            # -----------------------------------------------------------
            # If we see + or - followed by a digit/point, AND we just saw space/newline,
            # treat it as a signed number rather than an operator.
            if ch in ('+', '-') and space_skipped:
                nxt = self._peek(1)
                is_digit = nxt.isdigit()
                is_float = (nxt == '.' and self._peek(2).isdigit())
                
                if is_digit or is_float:
                    # It's a signed number!
                    tokens.append(self._read_number())
                    space_skipped = False
                    continue

            # identifiers & keywords A_z0
            if ch.isalpha() or ch == '_':
                tok = self._read_identifier()
                if tok.value.lower() in KEYWORDS:
                    tok.type = 'KEYWORD'
                tokens.append(tok)
                space_skipped = False
                continue

            # numbers, decimals, sci, 3i
            if ch.isdigit() or (ch == '.' and self._peek().isdigit()):
                tokens.append(self._read_number())
                space_skipped = False
                continue

            # -----------------------------------------------------------
            # Transpose vs String
            # -----------------------------------------------------------
            if ch == "'":
                is_transpose = False
                # [FIX] Transpose requires ADJACENCY. If space was skipped, it's a string.
                if tokens and not space_skipped:
                    prev = tokens[-1]
                    # Transpose valid after: ID, Number, ), ], }, '
                    if prev.type in ('ID', 'NUMBER') or prev.value in (')', ']', '}', "'"):
                        is_transpose = True
                
                if is_transpose:
                    tokens.append(Token('OP', "'", self.line))
                    self.pos += 1
                else:
                    tokens.append(self._read_string())
                space_skipped = False
                continue

            # anonymous function @
            if ch == '@':
                tokens.append(Token('AT', '@', self.line))
                self.pos += 1
                space_skipped = False
                continue

            # cell { } handled literally
            if ch in "{}":
                tokens.append(Token(ch, ch, self.line))
                self.pos += 1
                space_skipped = False
                continue

            # operators / punctuation / symbols
            if ch in "+-*/^=<>:;(),[]\\.~&|":
                tokens.append(self._read_operator())
                space_skipped = False
                continue

            raise SyntaxError(f"Unexpected character '{ch}' at line {self.line}")

        tokens.append(Token('EOF', '', self.line))
        return tokens

    # ---------------------------------------------------
    # Helpers
    # ---------------------------------------------------
    def _peek(self, offset: int = 1) -> str:
        p = self.pos + offset
        return self.text[p] if p < len(self.text) else ''

    def _skip_comment(self):
        while self.pos < len(self.text) and self.text[self.pos] != '\n':
            self.pos += 1

    def _skip_line_continuation(self):
        self.pos += 3
        while self.pos < len(self.text) and self.text[self.pos] != '\n':
            self.pos += 1

    def _read_identifier(self) -> Token:
        start = self.pos
        while self.pos < len(self.text) and (
            self.text[self.pos].isalnum() or self.text[self.pos] == '_'
        ):
            self.pos += 1
        return Token('ID', self.text[start:self.pos], self.line)

    def _read_number(self) -> Token:
        start = self.pos
        
        # [FIX] Consume sign if present (for signed numbers)
        if self.text[self.pos] in ('+', '-'):
            self.pos += 1

        # integer part
        while self.pos < len(self.text) and self.text[self.pos].isdigit():
            self.pos += 1

        # decimal part
        if self.pos < len(self.text) and self.text[self.pos] == '.':
            if not (self._peek(1) == '.' and self._peek(2) == '.'):
                self.pos += 1
                while self.pos < len(self.text) and self.text[self.pos].isdigit():
                    self.pos += 1

        # scientific notation
        if self.pos < len(self.text) and self.text[self.pos] in ('e', 'E'):
            p = self.pos + 1
            if p < len(self.text) and self.text[p] in ('+', '-'):
                p += 1
            if p < len(self.text) and self.text[p].isdigit():
                self.pos = p
                while self.pos < len(self.text) and self.text[self.pos].isdigit():
                    self.pos += 1

        # imaginary number (3i, 4j)
        if self.pos < len(self.text) and self.text[self.pos] in ('i', 'j'):
            nxt = self._peek(1)
            # ensure it's not part of a variable name
            if not nxt.isalnum() and nxt != '_':
                num = self.text[start:self.pos] + 'j'
                self.pos += 1
                return Token('NUMBER', num, self.line)

        return Token('NUMBER', self.text[start:self.pos], self.line)

    def _read_string(self) -> Token:
        self.pos += 1
        start = self.pos
        while self.pos < len(self.text) and self.text[self.pos] != "'":
            self.pos += 1
        val = self.text[start:self.pos]
        if self.pos < len(self.text):
            self.pos += 1
        return Token('STRING', val, self.line)

    def _read_operator(self) -> Token:
        ch = self.text[self.pos]
        nxt = self._peek()

        # [FIX] Handle .' (transpose)
        if ch == '.' and nxt in ('*', '/', '\\', '^', "'"): 
            op = ch + nxt
            self.pos += 2
            return Token('OP', op, self.line)

        # two-char ops == ~= <= >=
        if ch in ('=', '~', '<', '>') and nxt == '=':
            op = ch + nxt
            self.pos += 2
            return Token('OP', op, self.line)

        # [FIX] Handle && and ||
        if ch in ('&', '|') and nxt == ch:
            op = ch + nxt
            self.pos += 2
            return Token('OP', op, self.line)

        # lone char
        self.pos += 1
        if ch in "()[]{}.,;":
            return Token(ch, ch, self.line)

        # arithmetic + - * / \ ^ ~ & | < >
        return Token('OP', ch, self.line)