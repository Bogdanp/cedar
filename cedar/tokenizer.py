import re

from collections import namedtuple
from enum import Enum

from .errors import ParseError

TokenKind = Enum("TokenKind", (
    "enum union record function name cap_name qmark comma colon lparen rparen "
    "lbrace rbrace lbracket rbracket newline whitespace invalid eof"))
Token = namedtuple("Token", "kind value line column")
Spec = namedtuple("Spec", "kind re")


def tokenize(file_name, file_contents):
    """Convert an input string into a stream of Tokens.

    Parameters:
      file_name(str): Used when reporting errors.
      file_contents(str): -

    Raises:
      ParseError: Whenever an unexpected token is encountered.

    Returns:
      Token generator: -
    """
    line, index, column, column_end = 1, 0, 0, 0
    for match in _spec.finditer(file_contents):
        kind = match.lastgroup
        value = match.group(kind)
        column = match.start() - index
        column_end = match.end() - index

        kind = getattr(TokenKind, kind)
        if kind == TokenKind.newline:
            index = match.end()
            line += 1

        elif kind == TokenKind.whitespace:
            continue

        elif kind == TokenKind.invalid:
            message = "unexpected {!r}".format(value)
            raise ParseError(message, file_name, file_contents, line, column)

        yield Token(kind, value, line, column)

    yield Token(TokenKind.eof, None, line, column_end)


_spec = re.compile("|".join(r"(?P<{s.kind.name}>{s.re})".format(s=s) for s in (
    Spec(TokenKind.enum, r"enum"),
    Spec(TokenKind.union, r"union"),
    Spec(TokenKind.record, r"record"),
    Spec(TokenKind.function, r"fn"),
    Spec(TokenKind.name, r"[a-z_][a-zA-Z0-9_]*"),
    Spec(TokenKind.cap_name, r"[A-Z][a-zA-Z0-9_]*"),
    Spec(TokenKind.qmark, r"\?"),
    Spec(TokenKind.comma, r","),
    Spec(TokenKind.colon, r":"),
    Spec(TokenKind.lparen, r"\("),
    Spec(TokenKind.rparen, r"\)"),
    Spec(TokenKind.lbrace, r"\{"),
    Spec(TokenKind.rbrace, r"\}"),
    Spec(TokenKind.lbracket, r"\["),
    Spec(TokenKind.rbracket, r"\]"),
    Spec(TokenKind.whitespace, r"( +|//.*)"),
    Spec(TokenKind.newline, r"\n"),
    Spec(TokenKind.invalid, r"."),
)))
