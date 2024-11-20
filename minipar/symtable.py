"""
Módulo da Tabela de Símbolos e Variáveis

O módulo das tabelas define as classes que representam
o acesso as variáveis de acordo com seus escopos na análise
sintática e no módulo de execução
"""

from dataclasses import dataclass, field
from typing import Any, Optional, Union


@dataclass
class Symbol:
    """
    Classe que representa um Símbolo

    Attributes:
        var (string): nome da variável
        type (string): tipo da variável
    """

    var: str
    type: str


@dataclass
class SymTable:
    """
    Classe que representa a tabela de símbolos

    table (dict): tabela de símbolos
    prev (SymTable): referência â tabela de escopo maior
    """

    table: dict[str, Symbol] = field(default_factory=dict)
    prev: Optional["SymTable"] = None

    def insert(self, string: str, symbol: Symbol):
        """
        Insere um Símbolo na tabela e retorna o status da operação

        Returns:
            boolean: status da operação
        """
        if self.table.get(string):
            return False
        self.table[string] = symbol
        return True

    def find(self, string: str) -> Symbol | None:
        """
        Busca um símbolo na tabela pelo seu nome

        Returns:
            Symbol | None: Símbolo encontrado ou vazio
        """
        st = self
        while st:
            value = st.table.get(string)
            if value is None:
                st = st.prev
                continue
            return value


@dataclass
class VarTable:
    """
    Classe que representa a tabela de variáveis

    table (dict): tabela de variáveis
    prev (VarTable): referência â tabela de escopo maior
    """

    table: dict[str, Any] = field(default_factory=dict)
    prev: Optional["VarTable"] = None

    def find(self, string: str) -> Union["VarTable", None]:
        """
        Busca uma variável na tabela pelo seu nome

        Returns:
            VarTable | None: Tabela onde se encontra a variável ou vazio
        """

        st = self
        while st:
            value = st.table.get(string)
            if value is None:
                st = st.prev
                continue
            return st
