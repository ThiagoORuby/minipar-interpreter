import re
from abc import ABC, abstractmethod
from collections.abc import Generator
from dataclasses import dataclass, field

from minipar.token import TOKEN_REGEX, Token

type NextToken = Generator[tuple[Token, int], None, None]


class ILexer(ABC):

    @abstractmethod
    def scan(self) -> NextToken:
        pass


@dataclass
class Lexer(ILexer):
    data: str
    line: int = 1
    token_table: dict[str, str] = field(default_factory=dict)

    def __post_init__(self):
        # Adicionando tipos e valores booleanos
        self.token_table["number"] = "TYPE"
        self.token_table["bool"] = "TYPE"
        self.token_table["string"] = "TYPE"
        self.token_table["void"] = "TYPE"
        self.token_table["true"] = "TRUE"
        self.token_table["false"] = "FALSE"

        # Adicionando palavras reservadas
        self.token_table["func"] = "FUNC"
        self.token_table["while"] = "WHILE"
        self.token_table["if"] = "IF"
        self.token_table["else"] = "ELSE"
        self.token_table["return"] = "RETURN"
        self.token_table["break"] = "BREAK"
        self.token_table["continue"] = "CONTINUE"
        self.token_table["par"] = "PAR"
        self.token_table["seq"] = "SEQ"
        self.token_table["c_channel"] = "C_CHANNEL"
        self.token_table["s_channel"] = "S_CHANNEL"
        self.token_table["inline"] = "INLINE"

    def scan(self):
        compiled_regex = re.compile(TOKEN_REGEX)

        for match in compiled_regex.finditer(self.data):
            kind = match.lastgroup
            value = match.group()
            if kind == "WHITESPACE" or kind == "SCOMMENT":
                continue
            elif kind == "MCOMMENT":
                self.line += value.count("\n")
                continue
            elif kind == "NEWLINE":
                self.line += 1
                continue
            elif kind == "NAME":
                kind = self.token_table.get(value)
                if not kind:
                    kind = "ID"
            elif kind == "STRING":
                value = value.replace('"', '')
            elif kind == "OTHER":
                kind = value
            yield Token(kind, value), self.line  # type: ignore
