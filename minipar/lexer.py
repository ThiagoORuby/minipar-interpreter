"""
Módulo de Análise Léxica

O módulo de Análise Léxica conta com classes que possibilitam a
separação de um código da linguagem Minipar em um conjunto de tokens
"""

import re
from abc import ABC, abstractmethod
from collections.abc import Generator
from dataclasses import dataclass, field

from minipar.token import TOKEN_REGEX, Token

type NextToken = Generator[tuple[Token, int], None, None]


class ILexer(ABC):
    """
    Interface para a Análise Léxica
    """

    @abstractmethod
    def scan(self) -> NextToken:
        pass


@dataclass
class Lexer(ILexer):
    """
    Classe que implementa os métodos da interface de Análise Léxica

    Attributes:
        data (str): Código de entrada na linguagem Minipar
        line (int): Valor da linha atual da Análise
        token_table (dict): Tabela para tipos e palavras reservadas da linguagem
    """

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

    def scan(self):
        """
        Gera o próximo token a partir do código Minipar

        Yields:
            Token: Próximo token encontrado
            int: número da linha referente ao token
        """

        # Compila o conjunto de expressões regulares
        compiled_regex = re.compile(TOKEN_REGEX)

        # Itera sobre as correspondências encontradas no código
        for match in compiled_regex.finditer(self.data):

            # Obtém a tag e valor correspondentes ao padrão encontrado
            kind = match.lastgroup
            value = match.group()

            # Ignora espaços em branco e comentários
            if kind == "WHITESPACE" or kind == "SCOMMENT":
                continue
            elif kind == "MCOMMENT":
                # Contabiliza linhas para comentários multilinha
                self.line += value.count("\n")
                continue
            elif kind == "NEWLINE":
                # Contabliza quebras de linha
                self.line += 1
                continue
            elif kind == "NAME":
                # Verifica se um nome corresponde a um tipo ou keyword
                kind = self.token_table.get(value)
                # Caso contrário, tipifica como Identificador (variável)
                if not kind:
                    kind = "ID"
            elif kind == "STRING":
                # Remove aspas duplas da string
                value = value.replace('"', '')
            elif kind == "OTHER":
                # Tipifica outros padrões com o próprio valor
                kind = value

            # Gera o token e a linha correspondente
            yield Token(kind, value), self.line  # type: ignore
