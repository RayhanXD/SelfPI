"""Python token stream — identifiers, dots, parens, strings, comments.

Deterministic lexer. Language quirks live here (CLAUDE.md rule 5).
"""

from __future__ import annotations

from typing import Any

Token = dict[str, Any]


def tokenize(source: str) -> list[Token]:
    """Lex Python source into a token stream.

    Each token: {type, value, line, col, in_comment, in_string}
    Types: IDENT | DOT | LPAREN | RPAREN | LBRACE | RBRACE | LBRACKET | RBRACKET |
           COMMA | EQ | COLON | STRING | NUMBER | NEWLINE | COMMENT | OP | KEYWORD
    """
    tokens: list[Token] = []
    n = len(source)
    i = 0
    line = 1
    col = 1

    keywords = frozenset(
        {
            "import",
            "from",
            "as",
            "def",
            "class",
            "return",
            "if",
            "elif",
            "else",
            "for",
            "while",
            "with",
            "pass",
            "None",
            "True",
            "False",
            "and",
            "or",
            "not",
            "in",
            "is",
            "lambda",
            "yield",
            "async",
            "await",
        }
    )

    def emit(ttype: str, value: str, start_line: int, start_col: int, *, in_comment=False, in_string=False):
        tokens.append(
            {
                "type": ttype,
                "value": value,
                "line": start_line,
                "col": start_col,
                "in_comment": in_comment,
                "in_string": in_string,
            }
        )

    while i < n:
        ch = source[i]

        if ch == "\n":
            emit("NEWLINE", "\n", line, col)
            i += 1
            line += 1
            col = 1
            continue

        if ch in " \t\r":
            i += 1
            col += 1
            continue

        # Line comment
        if ch == "#":
            start_line, start_col = line, col
            j = i
            while j < n and source[j] != "\n":
                j += 1
            emit("COMMENT", source[i:j], start_line, start_col, in_comment=True)
            col += j - i
            i = j
            continue

        # String (including triple quotes)
        if ch in ("'", '"'):
            start_line, start_col = line, col
            quote = ch
            triple = source[i : i + 3] == quote * 3
            if triple:
                i += 3
                col += 3
                end = quote * 3
                buf = [end]
                while i < n:
                    if source[i : i + 3] == end:
                        buf.append(end)
                        i += 3
                        col += 3
                        break
                    if source[i] == "\n":
                        buf.append("\n")
                        i += 1
                        line += 1
                        col = 1
                    elif source[i] == "\\" and i + 1 < n:
                        buf.append(source[i : i + 2])
                        i += 2
                        col += 2
                    else:
                        buf.append(source[i])
                        i += 1
                        col += 1
                emit("STRING", "".join(buf), start_line, start_col, in_string=True)
            else:
                i += 1
                col += 1
                buf = [quote]
                while i < n and source[i] != quote:
                    if source[i] == "\\" and i + 1 < n:
                        buf.append(source[i : i + 2])
                        i += 2
                        col += 2
                    elif source[i] == "\n":
                        break
                    else:
                        buf.append(source[i])
                        i += 1
                        col += 1
                if i < n and source[i] == quote:
                    buf.append(quote)
                    i += 1
                    col += 1
                emit("STRING", "".join(buf), start_line, start_col, in_string=True)
            continue

        # Identifier / keyword
        if ch.isalpha() or ch == "_":
            start_line, start_col = line, col
            j = i + 1
            while j < n and (source[j].isalnum() or source[j] == "_"):
                j += 1
            value = source[i:j]
            ttype = "KEYWORD" if value in keywords else "IDENT"
            emit(ttype, value, start_line, start_col)
            col += j - i
            i = j
            continue

        # Number
        if ch.isdigit():
            start_line, start_col = line, col
            j = i + 1
            while j < n and (source[j].isdigit() or source[j] in ".eExX_"):
                j += 1
            emit("NUMBER", source[i:j], start_line, start_col)
            col += j - i
            i = j
            continue

        # Single-char punctuation
        start_line, start_col = line, col
        punct = {
            ".": "DOT",
            "(": "LPAREN",
            ")": "RPAREN",
            "{": "LBRACE",
            "}": "RBRACE",
            "[": "LBRACKET",
            "]": "RBRACKET",
            ",": "COMMA",
            "=": "EQ",
            ":": "COLON",
        }
        if ch in punct:
            emit(punct[ch], ch, start_line, start_col)
            i += 1
            col += 1
            continue

        emit("OP", ch, start_line, start_col)
        i += 1
        col += 1

    return tokens
