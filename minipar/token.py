from dataclasses import dataclass

TOKEN_PATTERNS = [
    ("NAME", r"[A-Za-z_][A-Za-z0-9_]*"),
    ("NUMBER", r"\b\d+\.\d+|\.\d+|\d+\b"),
    ("RARROW", r"->"),
    ("RDARROW", r"=>"),
    ("STRING", r'"([^"]*)"'),  # strings
    ("SCOMMENT", r"#.*"),
    ("MCOMMENT", r"/\*[\s\S]*?\*/"),
    ("OR", r"\|\|"),
    ("AND", r"&&"),
    ("EQ", r"=="),
    ("NEQ", r"!="),
    ("LTE", r"<="),
    ("GTE", r">="),
    ("NEWLINE", r"\n"),  # Nova linha (usada para separação de regras)
    ("WHITESPACE", r"\s+"),  # Espaços em branco
    ("OTHER", r"."),
]

STATEMENT_TOKENS = {
    "ID",
    "FUNC",
    "IF",
    "ELSE",
    "FOR",
    "WHILE",
    "RETURN",
    "BREAK",
    "CONTINUE",
    "SEQ",
    "PAR",
    "C_CHANNEL",
    "S_CHANNEL",
}

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

TOKEN_REGEX = '|'.join(
    f'(?P<{name}>{pattern})' for name, pattern in TOKEN_PATTERNS
)


@dataclass
class Token:
    tag: str
    value: str

    def __repr__(self):
        return f"{{{self.value}, {self.tag}}}"
