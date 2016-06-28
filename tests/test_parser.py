import pytest

from cedar import ParseError, parse
from cedar.ast import (
    Enum, Tag,
    Record, Attribute,
    Function, Parameter,
    Type, Union, Dict, List, Nullable
)

from .common import Module, table


def test_parse_errors_can_halt_execution():
    with pytest.raises(ParseError) as e:
        parse("record!")

    with pytest.raises(SystemExit):
        e.value.print_and_halt()


def test_tabs_are_not_allowed():
    with pytest.raises(ParseError) as e:
        parse("record A {\n\ta Int\n}")

    assert e.value.message == r"unexpected '\t'"


def test_unexpected_tokens_raise_errors():
    with pytest.raises(ParseError) as e:
        parse("record A! {}")

    assert e.value.message == "unexpected '!'"


def test_only_toplevel_declarations_are_allowed_in_a_module():
    with pytest.raises(ParseError) as e:
        parse("User")

    assert e.value.line == 1
    assert e.value.column == 4


def test_enums_cannnot_have_many_dangling_commas():
    with pytest.raises(ParseError) as e:
        parse("enum A {B, C,,}")

    assert e.value.line == 1
    assert e.value.column == 13


def test_unions_cannot_be_empty():
    with pytest.raises(ParseError):
        parse("union A {}")


def test_comments_are_ignored():
    table([
        (
            """
              // a comment

              enum A {}

              // another comment
            """,
            Module([Enum("A", [])])
        ),

        (
            """
              // an enum
              enum A { B }

              // a record
              record C {
                // a field
                d Int
              }
            """,
            Module([
                Enum("A", [Tag("B")]),
                Record("C", [Attribute("d", Type("Int"))])
            ])
        ),
    ])


def test_can_parse_modules():
    table([
        (
            "",
            Module([])
        )
    ])


def test_can_parse_enums():
    table([
        ("enum A {}", Enum("A", [])),
        ("enum A { B, C, D }", Enum("A", [Tag("B"), Tag("C"), Tag("D")])),

        (
            """
              enum A {
                B,

                C
              }
            """,
            Enum("A", [Tag("B"), Tag("C")])
        ),

        (
            """
              enum A {
                B,
                C,
              }
            """,
            Enum("A", [Tag("B"), Tag("C")])
        )
    ])


def test_can_parse_unions():
    table([
        ("union A { B, C }", Union("A", [Type("B"), Type("C")])),

        (
            """
              union A {
                B,
                C,
              }
            """,
            Union("A", [Type("B"), Type("C")])
        ),
    ])


def test_can_parse_records():
    table([
        (
            "record Unit {}",
            Record("Unit", [])
        ),

        (
            """
              record User {
                id Int
                name String
                email String
                age Int?
                friends [User]
              }
            """,
            Record(
                "User",
                [
                    Attribute("id", Type("Int")),
                    Attribute("name", Type("String")),
                    Attribute("email", Type("String")),
                    Attribute("age", Nullable(Type("Int"))),
                    Attribute("friends", List(Type("User"))),
                ]
            )
        ),

        (
            "record A { map {String: Int?} }",
            Record(
                "A",
                [
                    Attribute("map", Dict(Type("String"), Nullable(Type("Int"))))
                ]
            )
        )
    ])


def test_can_parse_functions():
    table([
        (
            "fn findAllUsers() [User]",
            Function("findAllUsers", [], List(Type("User")))
        ),

        (
            "fn findUser(id Int) User?",
            Function("findUser", [Parameter("id", Type("Int"))], Nullable(Type("User")))
        ),

        (
            "fn findAllResources(kind ResourceKind) Resource",
            Function(
                "findAllResources",
                [Parameter("kind", Type("ResourceKind"))],
                Type("Resource")
            )
        ),

        (
            [
                "fn findUsersByAge(comparator Comparator, age Int) [User]",
                "fn findUsersByAge(comparator Comparator, age Int,) [User]",
                """
                fn findUsersByAge(
                  comparator Comparator, age Int,
                ) [User]
                """,
                """
                fn findUsersByAge(
                  comparator Comparator,
                  age Int,
                ) [User]
                """,
                """
                fn findUsersByAge(
                  comparator Comparator,
                  age Int
                ) [User]
                """
            ],
            Function(
                "findUsersByAge",
                [Parameter("comparator", Type("Comparator")), Parameter("age", Type("Int"))],
                List(Type("User"))
            )
        )
    ])
