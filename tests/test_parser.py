import pytest

from cedar import ParseError, ast, parse
from cedar.ast import (
    Enum, Tag,
    Record, Attribute,
    Function, Parameter,
    Type, Union, Dict, List, Nullable
)

from functools import partial

Module = partial(ast.Module, "[STRING]")


def table(tests):
    for string, expected_result in tests:
        if isinstance(string, list):
            return table([(s, expected_result) for s in string])

        if not isinstance(expected_result, ast.Module):
            expected_result = Module([expected_result])

        assert parse(string, typecheck=False) == expected_result


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
        ("union A {}", Union("A", [])),
        ("union A { B, C }", Union("A", [Type("B"), Type("C")])),

        (
            """
              union A {
                B,
                C?,
                [D]
              }
            """,
            Union("A", [Type("B"), Nullable(Type("C")), List(Type("D"))])
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
