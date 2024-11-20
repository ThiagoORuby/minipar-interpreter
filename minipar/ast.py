"""
Módulo da Árvore Sintática Abstrata (AST)

O módulo da AST conta com uma estrutura de classes responsável
por representa o conjunto de declarações e expressões da linguagem
"""

from dataclasses import dataclass

from minipar.token import Token


class Node:
    """
    Classe que representa um Nó na AST
    """

    pass


@dataclass
class Statement(Node):
    """
    Classe que representa uma declaração
    """

    pass


@dataclass
class Expression(Node):
    """
    Classe que representa uma expressão

    Attributes:
        type (str): Tipo de retorno da expressão
        token (Token): Token capturado pela expressão
    """

    type: str
    token: Token

    @property
    def name(self) -> str | None:
        if self.token:
            return self.token.value


#### TYPES #####

type Body = list[Statement | Expression]  # corpo dos Statements
type Arguments = list[Expression]  # valor dos keywords
type Parameters = dict[
    str, tuple[str, Expression | None]
]  # estrutura dos parâmetros (key: type, default)

##### EXPRESSIONS #####


@dataclass
class Constant(Expression):
    pass


@dataclass
class ID(Expression):
    decl: bool = False


@dataclass
class Access(Expression):
    id: ID
    expr: Expression


@dataclass
class Logical(Expression):
    left: Expression
    right: Expression


@dataclass
class Relational(Expression):
    left: Expression
    right: Expression


@dataclass
class Arithmetic(Expression):
    left: Expression
    right: Expression


@dataclass
class Unary(Expression):
    expr: Expression


@dataclass
class Call(Expression):
    id: ID | None
    args: Arguments
    oper: str | None


##### STATEMENTS #####


@dataclass
class Module(Statement):
    stmts: Body | None


@dataclass
class Assign(Statement):
    left: Expression
    right: Expression


@dataclass
class Return(Statement):
    expr: Expression


@dataclass
class Break(Statement):
    pass


@dataclass
class Continue(Statement):
    pass


@dataclass
class FuncDef(Statement):
    name: str
    return_type: str
    params: Parameters
    body: Body


@dataclass
class If(Statement):
    condition: Expression
    body: Body
    else_stmt: Body | None


@dataclass
class While(Statement):
    condition: Expression
    body: Body


@dataclass
class Par(Statement):
    body: Body


@dataclass
class Seq(Statement):
    body: Body


@dataclass
class Channel(Statement):
    name: str
    _localhost: Expression
    _port: Expression

    @property
    def localhost(self):
        return self._localhost.token.value

    @property
    def localhost_node(self):
        return self._localhost

    @property
    def port(self):
        return self._port.token.value

    @property
    def port_node(self):
        return self._port


@dataclass
class SChannel(Channel):
    func_name: str
    description: Expression


@dataclass
class CChannel(Channel):
    pass
