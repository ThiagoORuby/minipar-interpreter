"""
Módulo de Análise Sintática

O módulo de Análise Sintática conta com classes que possibilitam a
geração da Árvore Sintática Abstrada através da análise da sequência
de tokens identificados na linguagem
"""

from abc import ABC, abstractmethod
from copy import deepcopy

from minipar import ast
from minipar import error as err
from minipar.lexer import Lexer, NextToken
from minipar.symtable import Symbol, SymTable
from minipar.token import DEFAULT_FUNCTION_NAMES, STATEMENT_TOKENS, Token


class IParser(ABC):
    """
    Interface para a Análise Sintática
    """

    @abstractmethod
    def match(self, tag: str) -> bool:
        pass

    @abstractmethod
    def start(self) -> ast.Module:
        pass


class Parser(IParser):
    """
    Classe que implementa os métodos da interface de Análise Sintática

    Args:
        lexer (Lexer): Instância da classe de Análise Léxica

    Attributes:
        lexer (NextToken): Gerador de tokens
        lookahead (Token): Token atual da análise
        lineno (int): Linha atual da análise
        symtable (Symtable): Tabéla de símbolos da análise
    """

    def __init__(self, lexer: Lexer):
        self.lexer: NextToken = lexer.scan()
        self.lookahead, self.lineno = next(self.lexer)
        self.symtable = SymTable()
        for func_name in DEFAULT_FUNCTION_NAMES.keys():
            self.symtable.insert(func_name, Symbol(func_name, "FUNC"))

    def match(self, tag: str) -> bool:
        """
        Verifica se a tag do lookahead é igual a tag de entrada
        e atualiza o lookahead caso haja correspondência

        Args:
            tag (str): Tag de verificação
        """
        if tag == self.lookahead.tag:
            # Se tag corresponde, tenta pegar o próximo token
            # ou retorna Token de EOF
            try:
                self.lookahead, self.lineno = next(self.lexer)
            except StopIteration:
                self.lookahead = Token("EOF", "EOF")
            return True
        return False

    def start(self) -> ast.Module:
        """
        Inicia a Análise Sintática e retorna a AST ao final

        Returns:
            Module: Árvore Sintática Abstrata identificada
        """
        return self.program()

    def program(self):
        # program -> stmts
        return ast.Module(stmts=self.stmts())

    def stmts(self):
        # stmts -> stmt stmts | Empty
        body: ast.Body = []
        while self.lookahead.tag in STATEMENT_TOKENS:
            body.append(self.stmt())

        if self.lookahead.tag not in {"}", "EOF"}:
            raise err.SyntaxError(
                self.lineno,
                f"{self.lookahead.value} não inicia uma instrução válida",
            )

        return body

    def stmt(self):
        match self.lookahead.tag:
            case "ID":
                # assignment -> local = expression
                left: ast.Expression = self.local()
                if isinstance(left, ast.Call):
                    return left
                if not self.match("="):
                    raise err.SyntaxError(
                        self.lineno,
                        f"Esperado = no lugar de {self.lookahead.value}",
                    )
                right: ast.Expression = self.disjunction()
                return ast.Assign(left=left, right=right)
            case "FUNC":
                # function_stmt -> func ID ( params ) -> TYPE block
                self.match("FUNC")
                name: str = self.var("FUNC")
                params: ast.Parameters = self.params()
                if not self.match("RARROW"):
                    raise err.SyntaxError(
                        self.lineno,
                        f"esperado -> no lugar de {self.lookahead.value}",
                    )
                _type: str = self.lookahead.value
                if not self.match("TYPE"):
                    raise err.SyntaxError(
                        self.lineno,
                        f"tipo {self.lookahead.value} de retorno inválido",
                    )
                body: ast.Body = self.block(params)
                return ast.FuncDef(
                    name=name,
                    return_type=_type.upper(),
                    params=params,
                    body=body,
                )
            case "RETURN":
                # return_stmt -> return disjunction
                self.match("RETURN")
                expr: ast.Expression = self.disjunction()
                return ast.Return(expr)
            case "BREAK":
                # break
                self.match("BREAK")
                return ast.Break()
            case "CONTINUE":
                # continue
                self.match("CONTINUE")
                return ast.Continue()
            case "IF":
                # if_stmt -> if ( expression ) block else block
                self.match("IF")
                if not self.match("("):
                    raise err.SyntaxError(
                        self.lineno,
                        f"esperando ( no lugar de {self.lookahead.value}",
                    )
                cond: ast.Expression = self.disjunction()
                if not self.match(")"):
                    raise err.SyntaxError(
                        self.lineno,
                        f"esperando ) no lugar de {self.lookahead.value}",
                    )
                body: ast.Body = self.block()
                _else = None
                # else_block -> else block | EMPTY
                if self.lookahead.tag == "ELSE":
                    self.match("ELSE")
                    _else = self.block()
                return ast.If(condition=cond, body=body, else_stmt=_else)
            case "WHILE":
                # while_stmt -> while ( expression ) block
                self.match("WHILE")
                if not self.match("("):
                    raise err.SyntaxError(
                        self.lineno,
                        f"esperando ( no lugar de {self.lookahead.value}",
                    )
                cond: ast.Expression = self.disjunction()
                if not self.match(")"):
                    raise err.SyntaxError(
                        self.lineno,
                        f"esperando ) no lugar de {self.lookahead.value}",
                    )
                body: ast.Body = self.block()
                return ast.While(condition=cond, body=body)
            case "SEQ":
                # seq_stmt -> seq block
                self.match("SEQ")
                return ast.Seq(body=self.block())
            case "PAR":
                # par_stmt -> par block
                self.match("PAR")
                return ast.Par(body=self.block())
            case "C_CHANNEL":
                # c_channel_stmt -> c_channel ID {STRING, NUMBER}
                self.match("C_CHANNEL")
                name: str = self.var("C_CHANNEL")
                if not self.match("{"):
                    raise err.SyntaxError(
                        self.lineno,
                        f"esperando {{ no lugar de {self.lookahead.value}",
                    )
                localhost: ast.Expression = self.ari()
                if not self.match(","):
                    raise err.SyntaxError(
                        self.lineno,
                        f"esperando , no lugar de {self.lookahead.value}",
                    )
                port: ast.Expression = self.ari()
                if not self.match("}"):
                    raise err.SyntaxError(
                        self.lineno,
                        f"esperando }} no lugar de {self.lookahead.value}",
                    )
                return ast.CChannel(
                    name=name, _localhost=localhost, _port=port
                )
            case "S_CHANNEL":
                # s_channel_stmt -> s_channel ID {ID, STRING, STRING, NUMBER}
                self.match("S_CHANNEL")
                name: str = self.var("S_CHANNEL")
                if not self.match("{"):
                    raise err.SyntaxError(
                        self.lineno,
                        f"esperando {{ no lugar de {self.lookahead.value}",
                    )
                func: str = self.var("REF")
                if not self.match(","):
                    raise err.SyntaxError(
                        self.lineno,
                        f"esperando , no lugar de {self.lookahead.value}",
                    )
                description: ast.Expression = self.ari()
                if not self.match(","):
                    raise err.SyntaxError(
                        self.lineno,
                        f"esperando , no lugar de {self.lookahead.value}",
                    )
                localhost: ast.Expression = self.ari()
                if not self.match(","):
                    raise err.SyntaxError(
                        self.lineno,
                        f"esperando , no lugar de {self.lookahead.value}",
                    )
                port: ast.Expression = self.ari()
                if not self.match("}"):
                    raise err.SyntaxError(
                        self.lineno,
                        f"esperando }} no lugar de {self.lookahead.value}",
                    )
                return ast.SChannel(
                    name=name,
                    _localhost=localhost,
                    _port=port,
                    func_name=func,
                    description=description,
                )
            case _:
                raise err.SyntaxError(
                    self.lineno,
                    f"{self.lookahead.value} não inicia instrução válida",
                )

    def block(self, params: ast.Parameters | None = None):
        # block -> { stmts }
        if not self.match("{"):
            raise err.SyntaxError(
                self.lineno, f"esperando {{ no lugar de {self.lookahead.value}"
            )

        ### ENTRANDO NUM CONTEXTO LOCAL ###
        saved = self.symtable
        self.symtable = SymTable(prev=saved)

        if params:
            for name, (_type, _) in params.items():
                self.symtable.insert(name, Symbol(name, _type))

        sts: ast.Body = self.stmts()

        if not self.match("}"):
            raise err.SyntaxError(
                self.lineno, f"esperando }} no lugar de {self.lookahead.value}"
            )

        ### SAINDO DO CONTEXTO LOCAL ###
        self.symtable = saved
        return sts

    def params(self):
        # parameters -> params | EMPTY
        parameters: ast.Parameters = {}

        if not self.match("("):
            raise err.SyntaxError(
                self.lineno, f"esperando ( no lugar de {self.lookahead.value}"
            )

        if self.lookahead.value != ")":
            # params -> param next_params
            name, data = self.param()
            if parameters.get(name):
                raise err.SyntaxError(
                    self.lineno,
                    f"parâmetro {name} já foi declarado no escopo da função",
                )
            parameters[name] = data

        # next_params -> , param next_params
        #               | EMPTY
        while True:
            if self.lookahead.tag == ",":
                self.match(",")
                name, data = self.param()
                if parameters.get(name):
                    raise err.SyntaxError(
                        self.lineno,
                        f"parâmetro {name} já foi declarado no escopo da função",
                    )
                parameters[name] = data
            else:
                break

        if not self.match(")"):
            raise err.SyntaxError(
                self.lineno, f"esperando ) no lugar de {self.lookahead.value}"
            )

        return parameters

    def param(self):
        # param -> ID : TYPE default
        name: str = self.lookahead.value
        if not self.match("ID"):
            raise err.SyntaxError(
                self.lineno, f"nome {name} inválido para um parâmetro"
            )
        if not self.match(":"):
            raise err.SyntaxError(
                self.lineno, f"esperado : no lugar de {self.lookahead.value}"
            )
        _type: str = self.lookahead.value
        if not self.match("TYPE"):
            raise err.SyntaxError(
                self.lineno,
                f"esperado um tipo no lugar de {self.lookahead.value}",
            )

        # default -> = disjunction
        #           | EMPTY
        default = None
        if self.lookahead.tag == "=":
            self.match("=")
            default = self.disjunction()
        return name, (_type.upper(), default)

    def args(self):
        # arguments -> args | EMPTY
        arguments: ast.Arguments = []
        if self.lookahead.tag != ")":
            # args -> arg next_args
            arguments.append(self.disjunction())

        # next_args -> , arg next_args
        #           | EMPTY
        while True:
            if self.lookahead.tag == ",":
                self.match(",")
                arguments.append(self.disjunction())
            else:
                break

        return arguments

    def disjunction(self):
        # disjunction -> conjunction lor
        # lor -> || conjunction lor
        #       | EMPTY
        left = self.conjunction()

        while True:
            token: Token = deepcopy(self.lookahead)

            if self.lookahead.tag == "OR":
                self.match("OR")
                right = self.conjunction()
                left = ast.Logical(
                    type="BOOL", token=token, left=left, right=right
                )
            else:
                break

        return left

    def conjunction(self):
        # conjunction -> equality land
        # land -> && equality land
        #       | EMPTY
        left = self.equality()

        while True:
            token: Token = deepcopy(self.lookahead)

            if self.lookahead.tag == "AND":
                self.match("AND")
                right = self.equality()
                left = ast.Logical(
                    type="BOOL", token=token, left=left, right=right
                )
            else:
                break

        return left

    def equality(self):
        # equality -> comparison eqdif
        # eqdif -> (== | !=) comparison eqdif
        #       | EMPTY
        left = self.comparison()

        while True:
            token: Token = deepcopy(self.lookahead)

            if self.lookahead.tag in ("EQ", "NEQ"):
                self.match(self.lookahead.tag)
                right = self.comparison()
                left = ast.Relational(
                    type="BOOL", token=token, left=left, right=right
                )
            else:
                break

        return left

    def comparison(self):
        # comparison -> ari comp
        # comp -> (>, <, >=, <=) ari comp
        #       | EMPTY
        left = self.ari()

        while True:
            token: Token = deepcopy(self.lookahead)

            if self.lookahead.tag in (">", "<", "GTE", "LTE"):
                self.match(self.lookahead.tag)
                right = self.ari()
                left = ast.Relational(
                    type="BOOL", token=token, left=left, right=right
                )
            else:
                break

        return left

    def ari(self):
        # ari -> term op
        # op -> (+ | -) ari op
        #       | EMPTY
        left = self.term()

        while True:
            token: Token = deepcopy(self.lookahead)

            if self.lookahead.tag in ("+", "-"):
                self.match(self.lookahead.tag)
                right = self.term()
                left = ast.Arithmetic(
                    type=left.type, token=token, left=left, right=right
                )
            else:
                break

        return left

    def term(self):
        # term -> unary mult
        # mult -> (* | / | %) unary mult
        #       | Empty
        left = self.unary()

        while True:
            token: Token = deepcopy(self.lookahead)

            if self.lookahead.tag in ("*", "/", "%"):
                self.match(self.lookahead.tag)
                right = self.unary()
                left = ast.Arithmetic(
                    type=left.type, token=token, left=left, right=right
                )
            else:
                break
        return left

    def unary(self):
        # unary -> (! | - ) unary
        #       | primary
        unary: ast.Expression

        if self.lookahead.tag in ("!", "-"):
            t: Token = deepcopy(self.lookahead)
            self.match(self.lookahead.tag)
            expr = self.unary()
            unary = ast.Unary(type="BOOL", token=t, expr=expr)
        else:
            unary = self.primary()

        return unary

    def local(self):
        # local -> ID local_op
        # local_op -> : TYPE
        #       | index local_op
        #       | . ID local_op
        #       | ( arguments )
        #       | EMPTY
        # index -> [ NUMBER ]
        match self.lookahead.tag:
            case "ID":
                token = deepcopy(self.lookahead)
                self.match("ID")
                # local_op -> : TYPE
                if self.lookahead.value == ":":
                    self.match(":")
                    _type = self.lookahead.value
                    if not self.match("TYPE"):
                        raise err.SyntaxError(
                            self.lineno,
                            f"esperando um tipo no lugar de {self.lookahead.value}",
                        )
                    if not self.symtable.insert(
                        token.value, Symbol(token.value, _type)
                    ):
                        raise err.SyntaxError(
                            self.lineno,
                            f"variável {token.value} já foi declarada neste escopo",
                        )
                    return ast.ID(type=_type.upper(), token=token, decl=True)

                s: Symbol | None = self.symtable.find(token.value)
                if not s:
                    raise err.SyntaxError(
                        self.lineno, f"variável {token.value} não declarada"
                    )
                _type = s.type
                expr1 = ast.ID(type=_type.upper(), token=token)
                operation = ""
                while True:
                    if self.lookahead.tag == "[":
                        self.match("[")
                        expr1 = ast.Access(
                            _type.upper(), token, expr1, self.ari()
                        )
                        if not self.match("]"):
                            raise err.SyntaxError(
                                self.lineno,
                                f"esperando ] no lugar de {self.lookahead.value}",
                            )
                    if self.lookahead.tag == ".":
                        self.match(".")
                        operation += self.lookahead.value
                        self.match(self.lookahead.tag)
                    if self.lookahead.tag == "(":
                        self.match("(")
                        args: ast.Arguments = self.args()
                        expr1 = ast.Call(
                            type="FUNC",
                            token=token,
                            id=expr1,  # type: ignore
                            oper=operation,
                            args=args,
                        )
                        if not self.match(")"):
                            raise err.SyntaxError(
                                self.lineno,
                                f"esperando ( no lugar de {self.lookahead.value}",
                            )
                        break
                    else:
                        break
                return expr1
            case _:
                raise err.SyntaxError(
                    self.lineno,
                    f"esperado um identificador no lugar de {self.lookahead.value}",
                )

    def primary(self):
        # primary -> ( disjunction )
        #       | local
        #       | NUMBER
        #       | STRING
        #       | TRUE
        #       | FALSE
        expr: ast.Expression
        match self.lookahead.tag:
            case "(":
                self.match("(")
                expr = self.disjunction()
                if not self.match(")"):
                    raise err.SyntaxError(
                        self.lineno,
                        f"esperando ) no lugar de {self.lookahead.value}",
                    )
            case "ID":
                expr = self.local()
            case "NUMBER":
                expr = ast.Constant(
                    type="NUMBER", token=deepcopy(self.lookahead)
                )
                self.match("NUMBER")
            case "STRING":
                expr = ast.Constant(
                    type="STRING", token=deepcopy(self.lookahead)
                )
                self.match("STRING")
            case "TRUE":
                expr = ast.Constant(
                    type="BOOL", token=deepcopy(self.lookahead)
                )
                self.match("TRUE")
            case "FALSE":
                expr = ast.Constant(
                    type="BOOL", token=deepcopy(self.lookahead)
                )
                self.match("FALSE")
            case _:
                raise err.SyntaxError(
                    self.lineno,
                    f"Uma expressão é esperada no lugar de {self.lookahead.value}",
                )
        return expr

    def var(self, id_type: str):
        # Representa um ID de referencia
        token: Token = deepcopy(self.lookahead)
        if not self.match("ID"):
            raise err.SyntaxError(
                self.lineno,
                f"esperado um identificador no lugar de {self.lookahead.value}",
            )
        s: Symbol | None = self.symtable.find(token.value)
        if id_type == "REF":
            if not s:
                raise err.SyntaxError(
                    self.lineno, f"função {token.value} não declarada"
                )
        elif s:
            raise err.SyntaxError(
                self.lineno,
                f"variável {token.value} com tipo {s.type} já existe",
            )
        self.symtable.insert(token.value, Symbol(token.value, id_type))
        return token.value
