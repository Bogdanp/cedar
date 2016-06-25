import math
import sys


class CedarError(Exception):
    """Base class for Cedar exceptions.

    Attributes:
      message(str): A description of the error that occurred.
      file_name(str): The name of the file in which the error occurred.
      file_contents(str): The input string that failed to parse.
      line(int): The line at which the error occurred.
      column(int): The column at which the error occurred.
    """

    error_type = None

    def __init__(self, message, file_name, file_contents, line, column):
        self.message = message
        self.file_name = file_name
        self.file_contents = file_contents
        self.line = line
        self.column = column

    def print_error(self):
        return _print_error(
            self.error_type, self.message,
            self.file_name, self.file_contents,
            self.line, self.column
        )

    def print_and_halt(self):
        """Pretty-print this error to stderr and halt program execution.
        """
        self.print_error()
        sys.exit(1)


class ParseError(CedarError):
    """Raised whenever an error is ecountered during parsing.
    """

    error_type = "Parse error"


class TypeError(CedarError):
    """Instantiated for individual type errors.  Never raised.
    """

    error_type = "Type error"


class TypeErrors(CedarError):
    """A collection of TypeErrors.  Raised when one or more type
    errors are found in a Module.

    Parameters:
      errors(TypeError list): -
    """

    def __init__(self, errors):
        self.errors = errors

    def print_and_halt(self):
        """Pretty-print all the type errors in the current instance
        and halt program execution.
        """
        for i, error in enumerate(self.errors):
            if i != 0:
                sys.stderr.write("\n\n")

            error.print_error()

        sys.exit(1)


def _print_error(tipe, message, file_name, file_contents, line, column):
    padding = int(math.log(line, 10) + 1)
    start = max(0, line - 5)
    lines = file_contents.split("\n")[start:line]

    def format_line(index, content):
        return "{index:>{padding}}| {content}".format(
            padding=padding,
            index=start + index + 1,
            content=content
        )

    sys.stderr.write("""\
{tipe} in {filename}:

{lines}
{caret}

{message}
""".format(
        tipe=tipe,
        message=message,
        filename=file_name, line=line, column=column,
        lines="\n".join(format_line(i, line) for i, line in enumerate(lines)),
        caret="-" * (column + padding + 2) + "^",
    ))
