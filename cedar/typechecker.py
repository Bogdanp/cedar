from multipledispatch import dispatch

from . import ast
from .errors import TypeError


_builtins = ["Bool", "Int", "Float", "String", "Timestamp"]
_builtins_p = " or ".join(_builtins)


class Typechecker:
    def __init__(self):
        self.builtin_types = _builtins
        self.known_types = set(_builtins)
        self.known_fns = set([])
        self.type_errors = []

    def signal_type_error(self, message, token):
        self.type_errors.append(TypeError(
            message,
            self.file_name, self.file_contents,
            token.line, token.column
        ))

    def declare_type(self, name, token):
        if name in self.known_types:
            self.signal_type_error("cannot redeclare type {!r}".format(name), token)
        else:
            self.known_types.add(name)

    def declare_fn(self, name, token):
        if name in self.known_fns:
            self.signal_type_error("cannot redeclare function {!r}".format(name), token)
        else:
            self.known_fns.add(name)

    @dispatch(ast.Type, object)
    def typecheck(self, node, token):
        if node.name not in self.known_types:
            self.signal_type_error("unknown type {!r}".format(node.name), token)
        return node

    @dispatch(ast.Dict, object)
    def typecheck(self, node, token):
        if node.keys_type.name != "String":
            self.signal_type_error("dict keys must be Strings", token)
        return node
