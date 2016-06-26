from . import ast
from .errors import ParseError, TypeErrors
from .tokenizer import TokenKind, tokenize
from .typechecker import Typechecker


def parse(source, *, filename="[STRING]", typecheck=True):
    """Parse the source into a Cedar Module.

    Parameters:
      source(str): The input string to parse.
      filename(str): The name of the file the input string was read from.
      typecheck(bool): Type errors are ignored if this is falsy.

    Raises:
      ParseError: If a syntax error has been encountered.
      TypeError: If one or more type errors have been encountered.

    Returns:
      Module: an AST representing the parsed source.
    """
    return _Parser(filename, source, typecheck).parse()


class _Parser(Typechecker):
    def __init__(self, file_name, file_contents, check_types):
        super().__init__()

        self.file_name = file_name
        self.file_contents = file_contents
        self.check_types = check_types
        self.tokens = tokenize(file_name, file_contents)
        self.token = next(self.tokens)

    def parse(self):
        module = self.parse_module()
        if self.check_types and self.type_errors:
            raise TypeErrors(self.type_errors)
        return module

    def parse_module(self):
        dispatch = {
            TokenKind.enum: self.parse_enum,
            TokenKind.union: self.parse_union,
            TokenKind.record: self.parse_record,
            TokenKind.function: self.parse_function
        }

        declarations = []
        while not self.peek(TokenKind.eof):
            self.skip_newlines()
            token = self.peek(*dispatch.keys())
            if not token:
                token = self.next()
                raise self.signal_parse_error(
                    "expected function, record or enum, got {.name}".format(token.kind),
                    token
                )

            declarations.append(dispatch[token.kind]())

        return ast.Module(self.file_name, declarations)

    def parse_enum(self):
        self.consume(TokenKind.enum)
        name = token = self.consume(TokenKind.cap_name)
        self.declare_type(token.value, token)
        self.consume(TokenKind.lbrace)

        tags = self.separated_by(
            kind=TokenKind.comma,
            parser=self.parse_tag,
            until=TokenKind.rbrace
        )
        self.skip_newlines()
        self.consume(TokenKind.rbrace)
        self.skip_newlines()

        return ast.Enum(name.value, tags)

    def parse_tag(self):
        return ast.Tag(self.consume(TokenKind.cap_name).value)

    def parse_union(self):
        self.consume(TokenKind.union)
        name = token = self.consume(TokenKind.cap_name)
        self.declare_type(token.value, token)
        self.consume(TokenKind.lbrace)

        self.skip_newlines()
        types = [self.parse_type_tag()]
        self.skip_one(TokenKind.comma)

        types += self.separated_by(
            kind=TokenKind.comma,
            parser=self.parse_type_tag,
            until=TokenKind.rbrace
        )
        self.skip_newlines()
        self.consume(TokenKind.rbrace)
        self.skip_newlines()

        return ast.Union(name.value, types)

    def parse_type_tag(self):
        token = self.consume(TokenKind.cap_name)
        return self.typecheck(ast.Type(token.value), token)

    def parse_record(self):
        self.consume(TokenKind.record)
        name = token = self.consume(TokenKind.cap_name)
        self.declare_type(token.value, token)
        self.consume(TokenKind.lbrace)

        attributes = []
        self.skip_newlines()
        while not self.peek(TokenKind.rbrace):
            self.skip_newlines()
            attributes.append(self.parse_attribute())
            if not self.peek(TokenKind.rbrace):
                self.consume(TokenKind.newline)

        self.skip_newlines()
        self.consume(TokenKind.rbrace)
        if not self.peek(TokenKind.eof):
            self.consume(TokenKind.newline)

        return ast.Record(name.value, attributes)

    def parse_attribute(self):
        token = self.consume(TokenKind.name, message="the name of an attribute")
        return ast.Attribute(token.value, self.parse_type())

    def parse_function(self):
        self.consume(TokenKind.function)
        name = token = self.consume(TokenKind.name)
        self.declare_fn(token.value, token)
        self.consume(TokenKind.lparen)

        parameters = self.separated_by(
            kind=TokenKind.comma,
            parser=self.parse_parameter,
            until=TokenKind.rparen
        )
        self.skip_newlines()
        self.consume(TokenKind.rparen)
        self.skip_newlines()

        return_type = self.parse_type()
        if not self.peek(TokenKind.eof):
            self.consume(TokenKind.newline)

        return ast.Function(name.value, parameters, return_type)

    def parse_parameter(self):
        token = self.consume(TokenKind.name, message="a name for the parameter")
        return ast.Parameter(token.value, self.parse_type())

    def parse_type(self):
        if self.peek(TokenKind.lbracket):
            tipe = self.parse_list()

        elif self.peek(TokenKind.lbrace):
            tipe = self.parse_dict()

        else:
            token = self.consume(TokenKind.cap_name, message="the name of a type")
            tipe = self.typecheck(ast.Type(token.value), token)

        if self.skip_one(TokenKind.qmark):
            return ast.Nullable(tipe)

        return tipe

    def parse_list(self):
        self.consume(TokenKind.lbracket)
        tipe = self.parse_type()
        self.consume(TokenKind.rbracket)
        return ast.List(tipe)

    def parse_dict(self):
        self.consume(TokenKind.lbrace)
        keys_type = token = self.consume(TokenKind.cap_name)
        self.consume(TokenKind.colon)
        values_type = self.parse_type()
        self.consume(TokenKind.rbrace)
        return self.typecheck(ast.Dict(ast.Type(keys_type.value), values_type), token)

    def signal_parse_error(self, message, token):
        raise ParseError(message, self.file_name, self.file_contents, token.line, token.column)

    def consume(self, *kinds, message=None):
        token = self.token
        if token.kind not in kinds:
            message = "expected {}, found {.name}".format(
                message or " or ".join(k.name for k in kinds),
                token.kind
            )
            raise self.signal_parse_error(message, token)

        self.next()
        return token

    def peek(self, *kinds):
        if self.token.kind in kinds:
            return self.token

        return None

    def next(self):
        try:
            self.token = token = next(self.tokens)
            return token
        except StopIteration:
            return self.token

    def skip_one(self, *kinds):
        if self.peek(*kinds):
            return self.next()

    def skip_many(self, *kinds):
        last = None
        while self.peek(*kinds):
            last = self.next()

        return last

    def skip_newlines(self):
        return self.skip_many(TokenKind.newline)

    def separated_by(self, *, kind, parser, until):
        elems = []
        while not self.peek(until):
            self.skip_newlines()
            if len(elems) > 0:
                self.consume(kind)

            self.skip_newlines()
            if self.peek(until):
                break

            elems.append(parser())
            self.skip_newlines()

        return elems
