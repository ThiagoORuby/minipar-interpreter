from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from minipar import ast
from minipar import error as err
from minipar.token import DEFAULT_FUNCTION_NAMES

# TODO:Tipo: verficação de compatibilidade de operadores (Arithmetic, Relational, Logic)
# TODO:Funções: verificar que funções estão sendo atribuidas a variável de mesmo retorno
# TODO:Funções: verificar se retorno da função possui mesmo tipo do declarado para retorno
# TODO:Funções: verificar se numero de argumentos da função da sendo passado corretamente
# TODO:Escopo: verificar se return está em função e break e continue em while/for


class ISemanticAnalyzer(ABC):

    @abstractmethod
    def visit(self, node: ast.Node):
        pass

    @abstractmethod
    def generic_visit(self, node: ast.Node):
        pass


@dataclass
class SemanticAnalyzer(ISemanticAnalyzer):

    context_stack: list[ast.Node] = field(default_factory=list)
    function_table: dict[str, ast.FuncDef] = field(default_factory=dict)

    def __post_init__(self):
        self.default_func_names = list(DEFAULT_FUNCTION_NAMES.keys())

    def visit(self, node: ast.Node):
        meth_name: str = f"visit_{type(node).__name__}"
        visitor = getattr(self, meth_name, self.generic_visit)
        return visitor(node)

    def generic_visit(self, node: ast.Node):

        # ENTRA NO CONTEXTO DO NÓ
        self.context_stack.append(node)

        for attr in dir(node):
            value = getattr(node, attr)
            if isinstance(value, list):
                for item in value:
                    if isinstance(item, ast.Node):
                        self.visit(item)
            elif isinstance(value, ast.Node):
                self.visit(node)

        # SAI DO CONTEXTO DO NÓ
        self.context_stack.pop()

    ###### VISIT STATEMENTS ######

    def visit_Assign(self, node: ast.Assign):
        left_type = self.visit(node.left)
        right_type = self.visit(node.right)

        if not isinstance(node.left, ast.ID):
            raise err.SemanticError(
                "atribuição precisa ser feita para uma variável"
            )
        # verifica se tipo do valor atribuido é equivalente ao tipo da variavel
        var: ast.ID = node.left
        if left_type != right_type:
            raise err.SemanticError(
                f"(Erro de Tipo) variável {var.token.value} espera {left_type}"
            )

    def visit_Return(self, node: ast.Return):

        # verifica se return está dentro de função
        if not any(
            isinstance(parent, ast.FuncDef) for parent in self.context_stack
        ):
            raise err.SemanticError(
                "return encontrado fora de uma declaração de função"
            )

        # verifica se retorno da função é do mesmo tipo da função
        function: ast.FuncDef = next(
            (n for n in self.context_stack[::-1] if isinstance(n, ast.FuncDef))
        )
        expr_type = self.visit(node.expr)

        if expr_type != function.return_type:
            raise err.SemanticError(
                f"retorno em {function.name} tem tipo diferente do definido"
            )

    def visit_Break(self, _: ast.Break):
        # verifica se break está dentro de while ou for
        if not any(
            isinstance(parent, ast.While) for parent in self.context_stack
        ):
            raise err.SemanticError(
                "break encontrado fora de uma declaração de um loop"
            )

    def visit_Continue(self, _: ast.Continue):
        # verifica se continue está dentro de while ou for
        if not any(
            isinstance(parent, ast.While) for parent in self.context_stack
        ):
            raise err.SemanticError(
                "continue encontrado fora de uma declaração de um loop"
            )

    def visit_FuncDef(self, node: ast.FuncDef):
        # proibe criação de funções dentro de if, for, while, func, par
        if any(
            isinstance(parent, (ast.If, ast.While, ast.Par))
            for parent in self.context_stack
        ):
            raise err.SemanticError(
                "não é possível declarar funções dentro de escopos locais"
            )

        if node.name not in self.function_table:
            self.function_table[node.name] = node

        self.generic_visit(node)

    def visit_block(self, block: ast.Body):
        for node in block:
            self.visit(node)

    def visit_If(self, node: ast.If):
        cond_type = self.visit(node.condition)

        if cond_type != "BOOL":
            raise err.SemanticError(
                f"esperado BOOL, mas encontrado {cond_type}"
            )

        self.context_stack.append(node)
        self.visit_block(node.body)
        if node.else_stmt:
            self.visit_block(node.else_stmt)
        self.context_stack.pop()

    def visit_While(self, node: ast.While):
        cond_type = self.visit(node.condition)

        if cond_type != "BOOL":
            raise err.SemanticError(
                f"esperado BOOL, mas encontrado {cond_type}"
            )

        self.context_stack.append(node)
        self.visit_block(node.body)
        self.context_stack.pop()

    def visit_Par(self, node: ast.Par):

        if any(not isinstance(inst, ast.Call) for inst in node.body):
            raise err.SemanticError(
                "esperado apenas funções em um bloco de execução paralela"
            )

    def visit_CChannel(self, node: ast.CChannel):
        localhost_type = self.visit(node._localhost)

        if localhost_type != "STRING":
            raise err.SemanticError(
                f"localhost em {node.name} precisa ser STRING"
            )

        port_type = self.visit(node._port)

        if port_type != "NUMBER":
            raise err.SemanticError(f"port em {node.name} precisa ser NUMBER")

    def visit_SChannel(self, node: ast.SChannel):

        func = self.function_table[node.func_name]

        if func.return_type != "STRING":
            raise err.SemanticError(
                f"função base de {node.name} precisa ter retorno STRING"
            )

        if (
            len(func.params) != 1
            or list(func.params.values())[0][0] != "STRING"
        ):
            raise err.SemanticError(
                f"função base de {node.name} precisa ter exatamente 1 parâmetro STRING"
            )

        description_type = self.visit(node.description)

        if description_type != "STRING":
            raise err.SemanticError(
                f"localhost em {node.name} precisa ser STRING"
            )

        localhost_type = self.visit(node._localhost)

        if localhost_type != "STRING":
            raise err.SemanticError(
                f"localhost em {node.name} precisa ser STRING"
            )

        port_type = self.visit(node._port)

        if port_type != "NUMBER":
            raise err.SemanticError(f"port em {node.name} precisa ser NUMBER")

    ###### VISIT EXPRESSIONS #######

    def visit_Constant(self, node: ast.Constant):
        return node.type

    def visit_ID(self, node: ast.ID):
        return node.type

    def visit_Access(self, node: ast.Access):
        if node.type != "STRING":
            raise err.SemanticError(
                "Acesso por index é válido apenas em strings"
            )
        return node.type

    def visit_Logical(self, node: ast.Logical):
        left_type = self.visit(node.left)
        right_type = self.visit(node.right)

        if left_type != "BOOL" or right_type != "BOOL":
            raise err.SemanticError(
                f"(Erro de Tipo) Esperado BOOL, mas encontrado {left_type} e {right_type} na operação {node.token.value}"
            )

        return "BOOL"

    def visit_Relational(self, node: ast.Relational):
        left_type = self.visit(node.left)
        right_type = self.visit(node.right)

        if node.token.value in {"==", "!="}:
            if left_type != right_type:
                raise err.SemanticError(
                    f"(Erro de Tipo) Esperado tipos iguais, mas encontrado {left_type} e {right_type} na operação {node.token.value}"
                )
        else:
            if left_type != "NUMBER" or right_type != "NUMBER":
                raise err.SemanticError(
                    f"(Erro de Tipo) Esperado NUMBER, mas encontrado {left_type} e {right_type} na operação {node.token.value}"
                )

        return "BOOL"

    def visit_Arithmetic(self, node: ast.Arithmetic):
        left_type = self.visit(node.left)
        right_type = self.visit(node.right)

        if node.token.value == "+":
            if left_type != right_type:
                raise err.SemanticError(
                    f"(Erro de Tipo) Esperado tipos iguais, mas encontrado {left_type} e {right_type} na operação {node.token.value}"
                )
        else:
            if left_type != "NUMBER" or right_type != "NUMBER":
                raise err.SemanticError(
                    f"(Erro de Tipo) Esperado NUMBER, mas encontrado {left_type} e {right_type} na operação {node.token.value}"
                )

        return left_type

    def visit_Unary(self, node: ast.Unary):
        expr_type = self.visit(node.expr)

        if node.token.tag == "-":
            if expr_type != "NUMBER":
                raise err.SemanticError(
                    f"(Erro de Tipo) Esperado NUMBER, mas encontrado {expr_type} na operação {node.token.value}"
                )
        elif node.token.tag == "!":
            if expr_type != "BOOL":
                raise err.SemanticError(
                    f"(Erro de Tipo) Esperado BOOL, mas encontrado {expr_type} na operação {node.token.value}"
                )

        return expr_type

    def visit_Call(self, node: ast.Call):
        func_name = node.oper if node.oper else node.token.value

        for arg in node.args:
            self.visit(arg)

        function: ast.FuncDef | None = self.function_table.get(str(func_name))

        if not function:
            if func_name not in self.default_func_names:
                raise err.SemanticError(f"função {func_name} não declarada")
            else:
                return DEFAULT_FUNCTION_NAMES[func_name]

        nondefault_params = sum(
            [value[1] is not None for value in function.params.values()]
        )
        call_args = len(node.args)

        # verificação de argumentos / parametros
        if nondefault_params > call_args:
            raise err.SemanticError(
                f"Esperado {nondefault_params} argumentos, mas encontrado {call_args}"
            )

        return function.return_type
