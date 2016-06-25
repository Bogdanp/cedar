import argparse
import functools
import sys

from . import CedarError, parse
from .languages import go


_languages = {
    "go": go.register
}


def main():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(
        title="commands",
        description="available Cedar commands")

    generate = subparsers.add_parser(
        "generate",
        help="generate source code from a Cedar input file")
    generate_subparsers = generate.add_subparsers(
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
                    module = parse(f.read(), filename=f)
                    return handler(arguments, module)
                except CedarError as e:
                    return e.print_and_halt()
        return wrapper

    generate.set_defaults(handle=handle_generate)

    sorted_languages = sorted(_languages.keys())
    for language in sorted_languages:
        register = _languages[language]
        subparser, handler = register(generate_subparsers)
        subparser.add_argument("filename", help="the Cedar file to generate source code from")
        subparser.set_defaults(handle=decorate_language(handler))

    arguments = parser.parse_args()
    if "handle" in arguments:
        return arguments.handle(arguments)

    parser.print_usage()
    return 0


if __name__ == "__main__":
    sys.exit(main())
