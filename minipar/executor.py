import socket
import threading
from abc import ABC, abstractmethod
from copy import deepcopy
from dataclasses import dataclass, field
from enum import Enum
from time import sleep

from minipar import ast
from minipar import error as err
from minipar.symtable import VarTable
from minipar.token import Token


class commands(Enum):
    BREAK = "BREAK"
    CONTINUE = "CONTINUE"
    RETURN = "RETURN"


class IExecutor(ABC):

    @abstractmethod
    def run(self, node: ast.Module):
        pass

    @abstractmethod
    def execute(self, node: ast.Node):
        pass

    @abstractmethod
    def enter_scope(self):
        pass

    @abstractmethod
    def exit_scope(self):
        pass


@dataclass
class Executor(IExecutor):

    var_table: VarTable = field(default_factory=VarTable)
    function_table: dict[str, ast.FuncDef] = field(default_factory=dict)
    connection_table: dict[str, socket.socket] = field(default_factory=dict)

    def __post_init__(self):
        self.default_functions = {
            "print": print,
            "input": input,
            "to_number": self.number,
            "to_string": str,
            "to_bool": bool,
            "sleep": sleep,
            "send": self.send,
            "close": self.close,
            "len": len,
            "isalpha": self.isalpha,
            "isnum": self.isnum,
        }

    def run(self, node: ast.Module):
        if node.stmts:
            for instruction in node.stmts:
                self.execute(instruction)

    def execute(self, node: ast.Node):
        meth_name: str = f"exec_{type(node).__name__}"
        execution = getattr(self, meth_name, None)

        if execution:
            return execution(node)

    def enter_scope(self):
        # print("ENTRANDO NUM ESCOPO")
        self.var_table = VarTable(prev=self.var_table)

    def exit_scope(self):
        if self.var_table.prev:
            # print("SAINDO DE UM ESCOPO")
            self.var_table = self.var_table.prev

    ###### EXECUTE STATEMENTS #####
    def exec_Assign(self, node: ast.Assign):
        right_value = self.execute(node.right)
        var_name = node.left.token.value
        decl = getattr(node.left, "decl")
        vt = self.var_table.find(var_name)
        if decl or not vt:
            self.var_table.table[var_name] = right_value
        else:
            vt.table[var_name] = right_value

        return var_name

    def exec_Return(self, node: ast.Return):
        return self.execute(node.expr)

    def exec_Break(self, _: ast.Break):
        return commands.BREAK

    def exec_Continue(self, _: ast.Continue):
        return commands.CONTINUE

    def exec_FuncDef(self, node: ast.FuncDef):
        if node.name not in self.function_table:
            self.function_table[node.name] = node

    def exec_block(self, block: ast.Body):
        ret = None
        for instruction in block:
            if isinstance(instruction, ast.Assign):
                self.exec_Assign(instruction)
            elif isinstance(instruction, ast.Return):
                return self.execute(instruction)
            else:
                ret = self.execute(instruction)
            if ret or ret in (commands.BREAK, commands.CONTINUE):
                return ret

        return None

    def exec_If(self, node: ast.If):
        condition = self.execute(node.condition)
        ret = None
        self.enter_scope()
        if condition:
            ret = self.exec_block(node.body)
        elif node.else_stmt:
            ret = self.exec_block(node.else_stmt)
        self.exit_scope()
        return ret

    def exec_While(self, node: ast.While):
        condition = self.execute(node.condition)
        self.enter_scope()
        while condition:
            ret = self.exec_block(node.body)
            condition = self.execute(node.condition)
            if ret == commands.BREAK:
                break
            elif ret == commands.CONTINUE:
                continue
            else:
                if ret:
                    return ret
        self.exit_scope()

    def exec_Par(self, node: ast.Par):
        threads = []

        for instruction in node.body:
            thread_var_table = deepcopy(self.var_table)
            thread_func_table = deepcopy(self.function_table)
            new_executor = Executor(thread_var_table, thread_func_table)
            t = threading.Thread(
                target=new_executor.execute, args=(instruction,)
            )
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

    def exec_Seq(self, _: ast.Seq):
        pass

    def exec_CChannel(self, node: ast.CChannel):
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect((node.localhost, int(node.port)))
        print(client.recv(2040).decode())
        self.connection_table[node.name] = client

    def exec_SChannel(self, node: ast.SChannel):
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.bind((node.localhost, int(node.port)))
        server.listen(10)
        conn, _ = server.accept()
        description = self.execute(node.description)
        if description:
            conn.send(description.encode("utf-8"))

        function: ast.FuncDef = self.function_table[node.func_name]
        while True:
            data = conn.recv(2048).decode()
            print(f"received: {data}")
            if not data:
                conn.close()
                break

            call = ast.Call(
                type=function.return_type,
                token=Token("ID", function.name),
                args=[
                    ast.Constant(type="STRING", token=Token("STRING", data))
                ],
                id=None,
                oper=None,
            )

            ret = self.exec_Call(call)

            conn.send(str(ret).encode("utf-8"))

    ######  PERSONALIZED FUNCTIONS ######

    def number(self, value):
        try:
            return int(value)
        except ValueError:
            return float(value)

    def isalpha(self, value):
        return str(value).isalpha()

    def isnum(self, value):
        return str(value).isnumeric()

    def send(self, conn_name: str, data: str):
        client = self.connection_table[conn_name]

        client.send(data.encode("utf-8"))

        return client.recv(2048).decode("utf-8")

    def close(self, conn_name: str):
        client = self.connection_table[conn_name]

        client.close()

    ###### EXECUTE EXPRESSIONS #####

    def exec_Constant(self, node: ast.Constant):
        match node.type:
            case "STRING":
                return node.token.value
            case "NUMBER":
                return eval(node.token.value)
            case "BOOL":
                return bool(node.token.value)
            case _:
                return node.token.value

    def exec_ID(self, node: ast.ID):
        var_name = node.token.value
        vt = self.var_table.find(var_name)
        if vt:
            return vt.table[var_name]
        else:
            raise err.RunTimeError(f"variável {var_name} não definida")

    def exec_Access(self, node: ast.Access):
        index = self.execute(node.expr)

        var_name = node.id.token.value
        vt = self.var_table.find(var_name)
        if vt:
            return vt.table[var_name][index]
        else:
            raise err.RunTimeError(f"variável {var_name} não definida")

    def exec_Logical(self, node: ast.Logical):
        left = self.execute(node.left)

        match node.token.value:
            case "&&":
                if left:
                    return self.execute(node.right)
                return left
            case "||":
                right = self.execute(node.right)
                return left or right
            case _:
                return

    def exec_Relational(self, node: ast.Relational):
        left = self.execute(node.left)
        right = self.execute(node.right)

        if left is None or right is None:
            return

        match node.token.value:
            case "==":
                return left == right
            case "!=":
                return left != right
            case ">":
                return left > right
            case "<":
                return left < right
            case ">=":
                return left >= right
            case "<=":
                return left <= right
            case _:
                return

    def exec_Arithmetic(self, node: ast.Arithmetic):
        left = self.execute(node.left)
        right = self.execute(node.right)

        if left is None or right is None:
            return

        match node.token.value:
            case "+":
                return left + right
            case "-":
                return left - right
            case "*":
                return left * right
            case "/":
                return left / right
            case "%":
                return left % right
            case _:
                return

    def exec_Unary(self, node: ast.Unary):
        expr = self.execute(node.expr)

        if expr is None:
            return

        match node.token.value:
            case "!":
                return not expr
            case "-":
                return expr * (-1)
            case _:
                return

    def exec_Call(self, node: ast.Call):

        func_name = node.oper if node.oper else node.token.value

        if func_name not in {"close", "send"}:
            if self.default_functions.get(func_name):
                args = [self.execute(arg) for arg in node.args]
                return self.default_functions[func_name](*args)
        else:
            conn_name = node.token.value
            if func_name == "send":
                args = [self.execute(arg) for arg in node.args]
                return self.default_functions[func_name](conn_name, *args)
            else:
                return self.default_functions[func_name](conn_name)

        function: ast.FuncDef | None = self.function_table.get(str(func_name))

        if not function:
            return

        self.enter_scope()

        for param in function.params.items():
            name, (_, default) = param
            if default:
                self.var_table.table[name] = self.execute(default)

        for param, arg in zip(function.params.items(), node.args):
            name, _ = param
            value = self.execute(arg)
            self.var_table.table[name] = value

        ret = self.exec_block(function.body)
        self.exit_scope()
        return ret
