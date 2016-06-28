import os

from cedar import ast, parse
from functools import partial

Module = partial(ast.Module, "[STRING]")


def rel(*xs):
    return os.path.join(os.path.abspath(os.path.dirname(__file__)), *xs)


def table(tests, typecheck=False):
    for string, expected_result in tests:
        if isinstance(string, list):
            return table([(s, expected_result) for s in string])

        if not isinstance(expected_result, ast.Module):
            expected_result = Module([expected_result])

        assert parse(string, typecheck=False) == expected_result
