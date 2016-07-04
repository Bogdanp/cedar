from collections import OrderedDict
from multipledispatch import dispatch

from .. import ast
from ..pretty import IndentConfig, blank, concat, text, line, block, pretty_print


def handle(arguments, module):
    """Handle a CLI call to the "generate go" command.

    Parameters:
      arguments(argparse.Namespace): Arguments to this subcommand as
        specified by the register function.
      module(Module): The Cedar Module to generate source code from.

    Returns:
      int: The command's exit code.
    """
    print(generate(
        module,
        package_name=arguments.package_name,
        server_name=arguments.server_name
    ))
    return 0


def register(parent):
    """Register an argument parser and handler function for the
    "generate go" command.

    Parameters:
      parent(argparse.ArgumentParser): The argument parser for the
        "generate" command.

    Returns:
      tuple: A tuple comprised of the "generate go" command's argument
      parser and its handler function.
    """
    parser = parent.add_parser("go")
    parser.add_argument(
        "--package-name",
        default="server",
        help="the generated source file's package"
    )
    parser.add_argument(
        "--server-name",
        default="Server",
        help="the name of the generated Server type"
    )
    return parser, handle


def generate(module, *, package_name="server", server_name="Server"):
    """Generate a Go source file containing the Server for a given
    Cedar Module.

    Parameters:
      module(ast.Module): The module to generate source code from.
      package_name(str): The generated source file's package.
      server_name(str): The name of the generated Server type.

    Returns:
      str: A string representing the generated Go source code.
    """
    assert isinstance(module, ast.Module)

    config = IndentConfig(0, 1, "\t")
    source = _Generator(
        package_name,
        server_name,
        module
    ).generate()

    return pretty_print(source, config)


def capitalize(s):
    return s[0].upper() + s[1:]


class _Generator:
    def __init__(self, package_name, server_name, module):
        self.package_name = package_name
        self.server_name = server_name
        self.module = module

        self.functions = OrderedDict()
        self.imports = set([
            "encoding/json",
            "errors",
            "net/http",
        ])

        self.enum_docs = []
        self.union_docs = []
        self.record_docs = []
        self.function_docs = []

    def generate(self):
        for decl in self.module.declarations:
            self.generate_decl(decl)

        return concat(
            text("package {}".format(self.package_name)),

            blank,
            line("import") + block((
                text('"{}"'.format(imp)) for imp in sorted(self.imports)
            ), tokens="()"),

            *self.enum_docs,
            *self.union_docs,
            *self.record_docs,
            *self.server_docs,
            *self.function_docs
        )

    @property
    def server_docs(self):
        ifs = [
            text("if req.Method != http.MethodPost") + block([
                text('err = errors.New("method not allowed")')
            ])
        ]
        for fn, (tipe, _) in self.functions.items():
            ifs.extend([
                text(' else if fn == "{}"'.format(fn)),
                block([
                    text("var request {}".format(tipe)),
                    text("err = dec.Decode(&request)"),
                    text("if err == nil") + block([
                        text("res, err = s.{}".format(fn)) + text("(req, &request)")
                    ])
                ])
            ])

        return [
            blank,
            line("type {} struct".format(self.server_name)),
            block(text("{} ".format(n)) + t for n, (_, t) in self.functions.items()),

            blank,
            line("func (s {sname}) ServeHTTP(rw http.ResponseWriter, req *http.Request)".format(
                sname=self.server_name)
            ),
            block([
                text("var err error"),
                text("var res interface{}"),
                text("enc := json.NewEncoder(rw)"),
                text("dec := json.NewDecoder(req.Body)"),
                text('fn := req.URL.Query().Get("fn")'),

                line(concat(
                    *ifs,
                    text(" else") + block([
                        text('err = errors.New("invalid function")')
                    ])
                )),

                line("if err != nil") + block([
                    text("rw.WriteHeader(http.StatusBadRequest)"),
                    text("err = enc.Encode(err.Error())"),
                    text("if err != nil") + block([
                        text("panic(err)")
                    ])
                ]) + text(" else") + block([
                    text("rw.WriteHeader(http.StatusOK)"),
                    text("err = enc.Encode(res)"),
                    text("if err != nil") + block([
                        text("panic(err)")
                    ])
                ]),
            ])
        ]

    @dispatch(ast.Enum)
    def generate_decl(self, enum):
        def tag(tag):
            return text('{tipe}{tag} {tipe} = "{tag}"'.format(
                tag=tag.name,
                tipe=enum.name
            ))

        self.enum_docs.append(concat(
            blank,
            line("type {} string".format(enum.name)),
            blank,
            line("var"),
            block((tag(node) for node in enum.tags), tokens="()"),
        ))

    @dispatch(ast.Union)
    def generate_decl(self, union):
        self.union_docs.append(concat(
            blank,
            line("type {} interface{{}}".format(union.name))
        ))

    @dispatch(ast.Record)
    def generate_decl(self, record):
        self.record_docs.append(concat(
            blank,
            line("type {} struct".format(record.name)),
            block(self.generate_node(node) for node in record.attributes),
        ))

    @dispatch(ast.Function)
    def generate_decl(self, function):
        name = function.name[0].upper() + function.name[1:]
        request_type = "{}Request".format(name)
        request = concat(
            blank,
            line("type {} struct".format(request_type)),
            block(self.generate_node(node) for node in function.parameters),
        )

        function_type = concat(
            text("func(*http.Request, *{}) ".format(request_type)),
            text("("),
            self.generate_node(function.return_type),
            text(", error)")
        )

        header = concat(
            blank,
            text("func (s *{sname}) Handle{name}(h ".format(
                sname=self.server_name,
                name=name
            )),
            function_type,
            text(") *{sname}".format(
                sname=self.server_name
            )),
        )

        declaration = concat(
            blank,
            header,
            block([
                text("s.{} = h".format(function.name)),
                text("return s")
            ]),
        )

        self.functions[function.name] = (request_type, function_type)
        self.record_docs.append(request)
        self.function_docs.append(declaration)

    @dispatch((ast.Attribute, ast.Parameter))
    def generate_node(self, node):
        if node.name.lower() == "id":
            name = "ID"
        else:
            name = capitalize(node.name)

        return concat(
            text("{name} ".format(name=name)),
            self.generate_node(node.type),
            text(' `json:"{}"`'.format(node.name))
        )

    @dispatch(ast.Type)
    def generate_node(self, tipe):
        try:
            return text({
                "Bool": "bool",
                "Float": "float64",
                "Int": "int",
                "String": "string",
                "Timestamp": "float64",
            }[tipe.name])
        except KeyError:
            return text(tipe.name)

    @dispatch(ast.Nullable)
    def generate_node(self, tipe):
        return text("*") + self.generate_node(tipe.type)

    @dispatch(ast.List)
    def generate_node(self, tipe):
        return text("[]") + self.generate_node(tipe.type)

    @dispatch(ast.Dict)
    def generate_node(self, tipe):
        return concat(
            text("map[string]"),
            self.generate_node(tipe.values_type)
        )

    @dispatch(ast.Union)
    def generate_node(self, tipe):
        return text("interface{}")
