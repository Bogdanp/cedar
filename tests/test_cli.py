import pytest
import sys

from contextlib import contextmanager
from cedar.cli import main
from unittest.mock import patch

from .common import rel

filename = rel("..", "examples", "todos", "todos.cedar")


@contextmanager
def arguments(*args):
    with patch.object(sys, "argv", list(args)):
        yield


def test_commands_are_routed_correctly():
    for cmd in ("elm", "go"):
        with arguments("cedar", "generate", cmd, filename):
            assert main() == 0


def test_generation_errors_exit():
    with pytest.raises(SystemExit),  \
         arguments("cedar", "generate", "go", rel("fixtures", "invalid.cedar")):  # noqa
        main()


def test_no_args_prints_usage():
    with arguments("cedar"):  # noqa
        assert main() == 0


def test_missing_lang_exits():
    with pytest.raises(SystemExit), arguments("cedar", "generate"):
        main()


def test_unknown_commands_exit():
    with pytest.raises(SystemExit), arguments("cedar", "generate", "foo", filename):
        main()
