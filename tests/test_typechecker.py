import pytest

from cedar import TypeErrors, parse
from cedar.ast import Enum, Union, Record, Attribute, Function, Type, List
from functools import partial

from . import common
from .common import Module

table = partial(common.table, typecheck=True)


def test_builtins_are_accepted():
    table([
        (
            """
              record A {
                a Bool
                b Timestamp
                c Int
                d Float
                e String
              }
            """,
            Record("A", [
                Attribute("a", Type("Bool")),
                Attribute("b", Type("Timestamp")),
                Attribute("c", Type("Int")),
                Attribute("d", Type("Float")),
                Attribute("e", Type("String")),
            ])
        )
    ])


def test_defining_types():
    table([
        (
            """
              enum Status { }

              record A {
                status Status
              }
            """,
            Module([
                Enum("Status", []),
                Record("A", [Attribute("status", Type("Status"))])
            ])
        ),

        (
            """
            record Post {
              id Int
              authorId Int
              title String
              content String
            }

            record Comment {
              id Int
              postId Int
              authorId Int
              content String
            }

            union Resource {
              Post, Comment
            }

            fn getResources() [Resource]
            """,
            Module([
                Record("Post", [
                    Attribute("id", Type("Int")),
                    Attribute("authorId", Type("Int")),
                    Attribute("title", Type("String")),
                    Attribute("content", Type("String")),
                ]),
                Record("Comment", [
                    Attribute("id", Type("Int")),
                    Attribute("postId", Type("Int")),
                    Attribute("authorId", Type("Int")),
                    Attribute("content", Type("String")),
                ]),
                Union("Resource", [
                    Type("Post"),
                    Type("Comment")
                ]),
                Function("getResources", [], List(Type("Resource")))
            ])
        ),
    ])


def test_unknown_types_are_rejected():
    with pytest.raises(TypeErrors):
        parse(
            """
              record A {
                a Idontexist
              }
            """
        )


def test_types_cannot_be_redeclared():
    with pytest.raises(TypeErrors):
        parse(
            """
              record A {
                a Idontexist
              }

              enum A { }
            """
        )


def test_functions_cannot_be_redeclared():
    with pytest.raises(TypeErrors):
        parse(
            """
              fn getUserIds() [Int]
              fn getUserIds() [Int]
            """
        )


def test_dict_keys_must_be_strings():
    with pytest.raises(TypeErrors):
        parse(
            """
              record A {
                d {Int: Float}
              }
            """
        )


def test_type_errors_are_accumulated():
    with pytest.raises(TypeErrors) as e:
        parse(
            """
              union Resource { A, B }

              record Resource {
              }
            """
        )

    assert len(e.value.errors) == 3


def test_type_errors_can_halt_execution():
    with pytest.raises(TypeErrors) as e:
        parse("union A { B, C }")

    with pytest.raises(SystemExit):
        e.value.print_and_halt()
