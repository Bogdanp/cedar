import operator

from collections import namedtuple
from functools import reduce
from multipledispatch import dispatch


class IndentConfig(namedtuple("IndentConfig", "offset indent_by indent_char")):
    def indent(self):
        return IndentConfig(
            self.offset + self.indent_by,
            self.indent_by,
            self.indent_char
        )

    def render(self):
        return self.indent_char * self.offset


class Doc:
    pass


class Nil(Doc, namedtuple("Nil", "")):
    def __add__(self, other):
        return other


class Text(Doc, namedtuple("Text", "value doc")):
    @dispatch(Nil)
    def __add__(self, _):
        return self

    @dispatch(Doc)
    def __add__(self, other):
        return Text(self.value, self.doc + other)


class Line(Doc, namedtuple("Line", "doc")):
    @dispatch(Nil)
    def __add__(self, _):
        return self

    @dispatch(Doc)
    def __add__(self, other):
        return Line(self.doc + other)


class Block(Doc, namedtuple("Block", "docs")):
    @dispatch(Nil)
    def __add__(self, _):
        return self

    @dispatch(Doc)
    def __add__(self, other):
        return Layout([self, other])


class Layout(Doc, namedtuple("Layout", "children")):
    @dispatch(Nil)
    def __add__(self, _):
        return self

    @dispatch((Text, Line, Block))
    def __add__(self, other):
        return Layout(self.children + [other])

    @dispatch(Doc)
    def __add__(self, other):
        return Layout(self.children + other.children)


@dispatch(Doc)
def line(doc):
    return Line(doc)


@dispatch(str)
def line(string):
    return Line(text(string))


def text(value, doc=Nil()):
    return Text(value, doc)

blank = line(text(""))


def concat(*children):
    return reduce(operator.add, children, Layout([]))


def block(children, tokens="{}"):
    block = Block([line(child) for child in children])
    if tokens is None:
        return block

    return concat(
        text(" "),
        text(tokens[0]),
        block,
        line(text(tokens[1]))
    )


@dispatch(Layout, IndentConfig)
def pretty_print(layout, config):
    return "".join(pretty_print(child, config) for child in layout.children)


@dispatch(Text, IndentConfig)
def pretty_print(text, config):
    return text.value + pretty_print(text.doc, config)


@dispatch(Line, IndentConfig)
def pretty_print(line, config):
    return "\n" + config.render() + pretty_print(line.doc, config)


@dispatch(Block, IndentConfig)
def pretty_print(block, config):
    return "".join(pretty_print(doc, config.indent()) for doc in block.docs)


@dispatch(Nil, IndentConfig)
def pretty_print(_, config):
    return ""
