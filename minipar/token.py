"""
Módulo de tokens

o módulo de tokens conta com a classe Token e constantes
necessárias para a análise léxica
"""

from dataclasses import dataclass

# Padrões dos tokens
TOKEN_PATTERNS = [
    ("NAME", r"[A-Za-z_][A-Za-z0-9_]*"),
    ("NUMBER", r"\b\d+\.\d+|\.\d+|\d+\b"),
    ("RARROW", r"->"),
    ("STRING", r'"([^"]*)"'),
    ("SCOMMENT", r"#.*"),
    ("MCOMMENT", r"/\*[\s\S]*?\*/"),
    ("OR", r"\|\|"),
    ("AND", r"&&"),
    ("EQ", r"=="),
    ("NEQ", r"!="),
    ("LTE", r"<="),
    ("GTE", r">="),
    ("NEWLINE", r"\n"),
    ("WHITESPACE", r"\s+"),
    ("OTHER", r"."),
]

# Nome dos Tokens de declarações
STATEMENT_TOKENS = {
    "ID",
    "FUNC",
    "IF",
    "ELSE",
    "WHILE",
    "RETURN",
    "BREAK",
    "CONTINUE",
    "SEQ",
    "PAR",
    "C_CHANNEL",
    "S_CHANNEL",
}

# Mapeamento de tipos de retorno para funções padrão da linguagem
DEFAULT_FUNCTION_NAMES = {
    "print": "VOID",
    "input": "STRING",
    "sleep": "VOID",
    "to_number": "NUMBER",
    "to_string": "STRING",
    "to_bool": "BOOL",
    "send": "STRING",
    "close": "VOID",
    "len": "NUMBER",
    "isalpha": "BOOL",
    "isnum": "BOOL",
}


# Regex para Análise Léxica
TOKEN_REGEX = '|'.join(
    f'(?P<{name}>{pattern})' for name, pattern in TOKEN_PATTERNS
)


@dataclass
class Token:
    """
    Classe que representa um Token (Lexema) da linguagem

    Attributes:
        tag (str): Tag do token
        value (str): Valor do token
    """

    tag: str
    value: str

    def __repr__(self):
        return f"{{{self.value}, {self.tag}}}"
