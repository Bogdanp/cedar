from multipledispatch import dispatch

from .. import ast
from ..pretty import IndentConfig, pretty_print, blank, block, concat, line, text


def handle(arguments, module):
    """Handle a CLI call to the "generate cedar" command.

    Parameters:
      arguments(argparse.Namespace): Arguments to this subcommand as
        specified by the register function.
      module(Module): The Cedar Module to generate source code from.

    Returns:
      int: The command's exit code.
    """
    print(format_module(module).strip())
    return 0


def register(parent):
    """Register an argument parser and handler function for the
    "generate cedar" command.

    Parameters:
      parent(argparse.ArgumentParser): The argument parser for the
        "cedar" command.

    Returns:
      tuple: A tuple comprised of the "generate cedar" command's
      argument parser and its handler function.
    """
    parser = parent.add_parser("cedar")
    return parser, handle


def format_module(module):
    assert isinstance(module, ast.Module)
    return pretty_print(_format(module), IndentConfig(0, 2, " "))


@dispatch(ast.Module)
def _format(module):
    return concat(*(_format(decl) for decl in module.declarations))


@dispatch(ast.Enum)
def _format(enum):
    return line("enum ") + text(enum.name) + block(
        text(tag.name) + text(",") for tag in enum.tags
    ) + blank


@dispatch(ast.Union)
def _format(union):
    return line("union ") + text(union.name) + block(
        text(tipe.name) + text(",") for tipe in union.types
    ) + blank


@dispatch(ast.Record)
def _format(record):
    def attr(attr):
        return concat(
            text(attr.name),
            text(" "),
            _format(attr.type)
        )

    return line("record ") + text(record.name) + block(
        attr(node) for node in record.attributes
    ) + blank


@dispatch(ast.Function)
def _format(function):
    def param(i, param):
        doc = concat(
            text(param.name),
            text(" "),
            _format(param.type)
        )

        if i != 0:
            return text(", ") + doc
        return doc

    parameters = (param(*pair) for pair in enumerate(function.parameters))
    return concat(
        line("fn "), text(function.name), text("("), *parameters, text(") "),
        _format(function.return_type)
    )


@dispatch(ast.Type)
def _format(tipe):
    return text(tipe.name)


@dispatch(ast.List)
def _format(node):
    return text("[") + _format(node.type) + text("]")


@dispatch(ast.Nullable)
def _format(node):
    return _format(node.type) + text("?")


@dispatch(ast.Dict)
def _format(node):
    return text("{String: ") + _format(node.type) + text("}")
