import argparse
import functools
import sys

from . import CedarError, parse, __version__
from .languages import cedar, elm, go


_languages = {
    "cedar": cedar.register,
    "elm": elm.register,
    "go": go.register,
}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--version", action="version", version=__version__)

    commands = parser.add_subparsers(
        title="commands",
        description="available Cedar commands")

    generate = commands.add_parser(
        "generate",
        help="generate source code from a Cedar input file")
    languages = generate.add_subparsers(
        title="languages",
        description="languages Cedar can generate source code for")

    def handle_generate(_):
        return generate.error("choose a language (choose from {})".format(
            ", ".join(repr(language) for language in sorted_languages)
        ))

    def decorate_language(handler):
        @functools.wraps(handler)
        def wrapper(arguments):
            with open(arguments.filename) as f:
                try:
                    module = parse(f.read(), filename=arguments.filename)
                    return handler(arguments, module)
                except CedarError as e:
                    return e.print_and_halt()
        return wrapper

    generate.set_defaults(handle=handle_generate)

    sorted_languages = sorted(_languages.keys())
    for language in sorted_languages:
        register = _languages[language]
        subparser, handler = register(languages)
        subparser.add_argument("filename", help="the Cedar file to generate source code from")
        subparser.set_defaults(handle=decorate_language(handler))

    arguments = parser.parse_args()
    if "handle" in arguments:
        return arguments.handle(arguments)

    parser.print_usage()
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
