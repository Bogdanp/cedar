from collections import defaultdict
from itertools import chain
from multipledispatch import dispatch

from .. import ast, pretty
from ..pretty import IndentConfig, blank, concat, text, line, pretty_print


def handle(arguments, module):
    """Handle a CLI call to the "generate elm" command.

    Parameters:
      arguments(argparse.Namespace): Arguments to this subcommand as
        specified by the register function.
      module(Module): The Cedar Module to generate source code from.

    Returns:
      int: The command's exit code.
    """
    print(generate(
        module,
        module_name=arguments.module_name,
    ))
    return 0


def register(parent):
    """Register an argument parser and handler function for the
    "generate elm" command.

    Parameters:
      parent(argparse.ArgumentParser): The argument parser for the
        "generate" command.

    Returns:
      tuple: A tuple comprised of the "generate elm" command's argument
      parser and its handler function.
    """
    parser = parent.add_parser("elm")
    parser.add_argument(
        "--module-name",
        default="Api.Client",
        help="the generated source file's fully-qualified module"
    )
    return parser, handle


def generate(module, *, module_name="Api.Client"):
    """Generate an Elm source file containing the Client for a given
    Cedar Module.

    Parameters:
      module(ast.Module): The module to generate source code from.
      module_name(str): The generated source file's fully-qualified
        module name.

    Returns:
      str: A string representing the generated Go source code.
    """
    assert isinstance(module, ast.Module)

    config = IndentConfig(0, 4, " ")
    source = _Generator(
        module_name,
        module
    ).generate()

    return pretty_print(source, config)


def block(children):
    return pretty.block(children, tokens=None)


class _Generator:
    def __init__(self, module_name, module):
        self.module_name = module_name
        self.module = module

        self.decoders = {}
        self.encoders = {}

        self.imports = set([
            ("Date", None, ("Date",)),
            ("Dict", None, ("Dict",)),
            ("HttpBuilder", "HB", None),
            ("Json.Decode", "JD", ("Decoder", "(:=)")),
            ("Json.Decode.Extra", None, ("(|:)", "date")),
            ("Json.Encode", "JE", None),
            ("Task", None, ("Task",)),
            ("Time", None, ("Time",)),
        ])

        self.enum_exports = set([])
        self.enum_docs = []
        self.enum_tags = defaultdict(dict)

        self.union_exports = set([])
        self.union_docs = []
        self.union_tags = defaultdict(dict)

        self.record_exports = set(["ClientConfig"])
        self.record_docs = []

        self.function_exports = set(["defaultConfig"])
        self.function_docs = []

    def generate(self):
        for decl in self.module.declarations:
            self.generate_decl(decl)

        exports = []
        sum_types = sorted(chain(self.enum_exports, self.union_exports))
        for i, export in enumerate(sum_types):
            doc = text(export + "(..)")
            if i != 0:
                doc = line(", ") + doc
            exports.append(doc)

        functions = sorted(chain(self.record_exports, self.function_exports))
        for i, export in enumerate(functions, len(sum_types)):
            doc = text(export)
            if i != 0:
                doc = line(", ") + doc
            exports.append(doc)

        return concat(
            text("module {} exposing".format(self.module_name)) + block([
                text("( ") + concat(*exports),
                text(")")
            ]),

            *self.import_docs,
            *self.client_docs,
            *self.enum_docs,
            *self.union_docs,
            *self.record_docs,
            *self.function_docs,
        )

    @property
    def import_docs(self):
        yield blank

        for (module, alias, funcs) in sorted(self.imports):
            imp = line("import " + module)
            if alias is not None:
                imp += text(" as " + alias)

            if funcs is not None:
                imp += text(" exposing (") + concat(*(
                    text(f) if i == 0 else text(", " + f) for i, f in enumerate(funcs)
                )) + text(")")

            yield imp

    @property
    def client_docs(self):
        return [
            blank, blank,
            line("type alias ClientConfig =") + block([
                text("{ endpoint : String"),
                text(", timeout : Time"),
                text(", withAuth : HB.RequestBuilder -> HB.RequestBuilder "),
                text("}")
            ]),

            blank, blank,
            line("defaultConfig : String -> ClientConfig"),
            line("defaultConfig endpoint =") + block([
                text("ClientConfig endpoint (Time.second * 5) identity")
            ]),

            blank, blank,
            line("decodeDate___ : Decoder Date"),
            line("decodeDate___ = ") + block([
                text("JD.map Date.fromTime JD.float")
            ]),

            blank, blank,
            line("encodeDate___ : Date -> JE.Value"),
            line("encodeDate___ = ") + block([
                text("Date.toTime >> JE.float")
            ]),

            blank, blank,
            line("encodeDict___ : (a -> JE.Value) -> Dict String a -> JE.Value"),
            line("encodeDict___ f = ") + block([
                text(r"Dict.toList >> List.map (\(k, v) -> (k, f v)) >> JE.object")
            ]),

            blank, blank,
            line("encodeMaybe___ : (a -> JE.Value) -> Maybe a -> JE.Value"),
            line("encodeMaybe___ f = ") + block([
                text("Maybe.map f >> Maybe.withDefault JE.null")
            ]),
        ]

    @dispatch(ast.Enum)
    def generate_decl(self, enum):
        def tag(i, tag):
            self.enum_tags[enum.name][tag.name] = name = enum.name + tag.name

            if i == 0:
                return text("= " + name)
            return text("| " + name)

        self.enum_exports.add(enum.name)
        self.enum_docs.append(concat(
            blank, blank,
            line("type {}".format(enum.name)),
            block(tag(*pair) for pair in enumerate(enum.tags)),

            *self.generate_encoder(enum),
            *self.generate_decoder(enum),
        ))

    @dispatch(ast.Union)
    def generate_decl(self, union):
        def tipe(i, tipe):
            self.union_tags[union.name][tipe.name] = name = union.name + tipe.name

            if i == 0:
                return text("= " + name + " " + tipe.name)
            return text("| " + name + " " + tipe.name)

        self.union_exports.add(union.name)
        self.union_docs.append(concat(
            blank, blank,
            line("type {}".format(union.name)),
            block(tipe(*pair) for pair in enumerate(union.types)),

            *self.generate_encoder(union),
            *self.generate_decoder(union),
        ))

    @dispatch(ast.Record)
    def generate_decl(self, record):
        attributes = []
        for i, attribute in enumerate(record.attributes):
            attr = text("{}: ".format(attribute.name)) + self.generate_node(attribute.type)
            if i != 0:
                attr = line(", ") + attr

            attributes.append(attr)

        self.record_exports.add(record.name)
        self.record_docs.append(concat(
            blank, blank,
            line("type alias {} =".format(record.name)),
            block([
                text("{ ") + concat(*attributes),
                text("}")
            ]),

            *self.generate_encoder(record),
            *self.generate_decoder(record),
        ))

    @dispatch(ast.Function)
    def generate_decl(self, function):
        param_names = ("config__ " + " ".join(p.name for p in function.parameters)).strip()
        param_types = concat(
            *(text(" -> ") + self.generate_node(p.type) for p in function.parameters)
        )
        return_type = concat(
            text(" -> Task (HB.Error String) (HB.Response "),
            self.generate_node(function.return_type),
            text(")")
        )

        self.function_exports.add(function.name)
        self.function_docs.append(concat(
            blank, blank,
            line("{name} : ClientConfig".format(name=function.name)) + param_types + return_type,
            line("{name} {params} = ".format(name=function.name, params=param_names)),
            block([
                text("let") + block([
                    text("req__ = ") + block([
                        text("JE.object") + block([
                            text("[ ") + concat(*(
                                self.generate_encoder("", *pair) for pair in enumerate(function.parameters))
                            ),
                            text("]")
                        ])
                    ]),

                    line("res__ = ") + block([
                        self.generate_decoder(function.return_type)
                    ])
                ]),
                text("in") + block([
                    text('HB.url config__.endpoint [("fn", "{}")]'.format(function.name)) + block([
                        text("|> HB.post"),
                        text("|> config__.withAuth"),
                        text('|> HB.withHeader "Content-type" "application/json"'),
                        text("|> HB.withJsonBody req__"),
                        text("|> HB.withTimeout config__.timeout"),
                        text("|> HB.send (HB.jsonReader res__) HB.stringReader")
                    ])
                ])
            ])
        ))

    @dispatch(ast.Type)
    def generate_node(self, tipe):
        try:
            return text({
                "Timestamp": "Date",
            }[tipe.name])
        except KeyError:
            return text(tipe.name)

    @dispatch(ast.Nullable)
    def generate_node(self, tipe):
        return text("(Maybe ") + self.generate_node(tipe.type) + text(")")

    @dispatch(ast.List)
    def generate_node(self, tipe):
        return text("(List ") + self.generate_node(tipe.type) + text(")")

    @dispatch(ast.Dict)
    def generate_node(self, tipe):
        self.imports.add(("Dict", None, ("Dict",)))
        return concat(
            text("Dict String "),
            self.generate_node(tipe.values_type)
        )

    def generate_encoder_name(self, node):
        self.encoders[node.name] = name = "encode" + node.name + "__"
        return name

    def generate_decoder_name(self, node):
        self.decoders[node.name] = name = "decode" + node.name + "__"
        return name

    @dispatch(ast.Enum)
    def generate_encoder(self, enum):
        def tag(tag):
            name = self.enum_tags[enum.name][tag.name]
            return text('{name} -> JE.string "{tag}"'.format(tag=tag.name, name=name))

        encoder_name = self.generate_encoder_name(enum)
        return [
            blank, blank,
            line("{name} : {enum} -> JE.Value".format(name=encoder_name, enum=enum.name)),
            line("{name} tag =".format(name=encoder_name)),
            block([
                text("case tag of") + block(
                    tag(node) for node in enum.tags
                ),
            ])
        ]

    @dispatch(ast.Union)
    def generate_encoder(self, union):
        def tipe(tipe):
            name = self.union_tags[union.name][tipe.name]
            return text(name + " x -> ") + self.generate_encoder(tipe) + text(" x")

        encoder_name = self.generate_encoder_name(union)
        return [
            blank, blank,
            line("{name} : {union} -> JE.Value".format(name=encoder_name, union=union.name)),
            line("{name} tag =".format(name=encoder_name)),
            block([
                text("case tag of") + block(
                    tipe(node) for node in union.types
                )
            ])
        ]

    @dispatch(ast.Record)
    def generate_encoder(self, record):
        encoder_name = self.generate_encoder_name(record)
        return [
            blank, blank,
            line("{name} : {record} -> JE.Value".format(name=encoder_name, record=record.name)),
            line("{name} record =".format(name=encoder_name)),
            block([
                text("JE.object") + block([
                    text("[ ") + concat(*(
                        self.generate_encoder("record.", *pair) for pair in enumerate(record.attributes)
                    )),
                    text("]")
                ])
            ])
        ]

    @dispatch(str, int, (ast.Attribute, ast.Parameter))
    def generate_encoder(self, prefix, i, node):
        doc = text('("{}", '.format(node.name)) + self.generate_encoder(node.type)
        if i != 0:
            doc = line(", ") + doc

        return doc + text(" {prefix}{name})".format(
            prefix=prefix,
            name=node.name
        ))

    @dispatch(ast.Type)
    def generate_encoder(self, tipe):
        try:
            return text({
                "Bool": "JE.bool",
                "Int": "JE.int",
                "Float": "JE.float",
                "String": "JE.string",
                "Timestamp": "encodeDate___",
            }[tipe.name])
        except KeyError:
            return text(self.encoders[tipe.name])

    @dispatch(ast.Nullable)
    def generate_encoder(self, tipe):
        return text("(encodeMaybe___ ") + self.generate_encoder(tipe.type) + text(")")

    @dispatch(ast.List)
    def generate_encoder(self, tipe):
        return text("(JE.list ") + self.generate_encoder(tipe.type) + text(")")

    @dispatch(ast.Dict)
    def generate_encoder(self, tipe):
        return text("(encodeDict___ ") + self.generate_encoder(tipe.values_type) + text(")")

    @dispatch(ast.Enum)
    def generate_decoder(self, enum):
        tags = []
        for tag in enum.tags:
            name = self.enum_tags[enum.name][tag.name]
            tags.append(text('"{tag}" -> Ok {name}'.format(tag=tag.name, name=name)))

        decoder_name = self.generate_decoder_name(enum)
        return [
            blank, blank,
            line("{name} : Decoder {enum}".format(name=decoder_name, enum=enum.name)),
            line("{name} =".format(name=decoder_name)),
            block([
                text("let") + block([
                    text("dec s = ") + block([
                        text("case s of") + block(tags + [
                            text('_ -> Err "invalid {enum}"'.format(enum=enum.name))
                        ])
                    ])
                ]),
                text("in") + block([
                    text("JD.customDecoder JD.string dec")
                ])
            ]),
        ]

    @dispatch(ast.Union)
    def generate_decoder(self, union):
        def tipe(i, tipe):
            name = self.union_tags[union.name][tipe.name]
            doc = text("JD.map {} ".format(name)) + self.generate_decoder(tipe)
            if i != 0:
                return line(", ") + doc
            return doc

        decoder_name = self.generate_decoder_name(union)
        return [
            blank, blank,
            line("{name} : Decoder {union}".format(name=decoder_name, union=union.name)),
            line("{name} =".format(name=decoder_name)),
            block([
                text("JD.oneOf") + block([
                    text("[ ") + concat(*(tipe(*pair) for pair in enumerate(union.types))),
                    text("]")
                ])
            ]),
        ]

    @dispatch(ast.Record)
    def generate_decoder(self, record):
        def attr(attr):
            decoder = self.generate_decoder(attr.type)
            return text('|: ("{}" := '.format(attr.name)) + decoder + text(")")

        decoder_name = self.generate_decoder_name(record)
        return [
            blank, blank,
            line("{name} : Decoder {record}".format(name=decoder_name, record=record.name)),
            line("{name} =".format(name=decoder_name)),
            block([
                text("JD.succeed " + record.name) + block(
                    attr(node) for node in record.attributes
                )
            ]),
        ]

    @dispatch(ast.Type)
    def generate_decoder(self, tipe):
        try:
            return text({
                "Bool": "JD.bool",
                "Int": "JD.int",
                "Float": "JD.float",
                "String": "JD.string",
                "Timestamp": "decodeDate___",
            }[tipe.name])
        except KeyError:
            return text(self.decoders[tipe.name])

    @dispatch(ast.Nullable)
    def generate_decoder(self, tipe):
        return text("(JD.maybe ") + self.generate_decoder(tipe.type) + text(")")

    @dispatch(ast.List)
    def generate_decoder(self, tipe):
        return text("(JD.list ") + self.generate_decoder(tipe.type) + text(")")

    @dispatch(ast.Dict)
    def generate_decoder(self, tipe):
        return text("(JD.dict ") + self.generate_decoder(tipe.values_type) + text(")")
