import json
import os
import requests
import shlex
import yaml

from cedar import cli
from collections import namedtuple
from functools import partial
from glob import iglob
from subprocess import PIPE, STDOUT, Popen

from . import common
from .common import arguments

rel = partial(common.rel, "fixtures", "codegen")


class Config(namedtuple("Config", "root endpoint targets commands entrypoint cases")):
    def test(self, capsys):
        self.build_targets(capsys)
        proc = self.run_commands()

        try:
            self.run_cases()
        finally:
            proc.terminate()

    def build_targets(self, capsys):
        for target in self.targets:
            command = shlex.split(target["command"]) + [rel(target["in"])]
            filename = target["out"]

            with open(rel(filename), "w") as f, arguments(*command):
                cli.main()
                output, _ = capsys.readouterr()
                f.write(output)

    def run_commands(self):
        popen = partial(Popen, cwd=rel(self.root))
        for command in self.commands:
            assert popen(shlex.split(command)).wait() == 0

        proc = popen(shlex.split(self.entrypoint), stdout=PIPE, stderr=STDOUT)
        while True:
            line = proc.stdout.readline()
            if b"listening" in line.lower():
                return proc

    def run_cases(self):
        for case in self.cases:
            description = case.get("description")
            if description is not None:
                print("Running test case: {!r}".format(description))

            request = case["request"]
            expected = case["response"]
            response = requests.post(
                self.endpoint,
                params={"fn": request["fn"]},
                data=json.dumps(request["data"])
            )

            if "code" in expected:
                assert expected["code"] == response.status_code

            if "data" in expected:
                assert expected["data"] == response.json()


test_template = """
def test_{name}(capsys):
  return configs[{name!r}].test(capsys)
"""

configs = {}
for filename in iglob(rel("*.yaml")):
    with open(filename) as f:
        name = os.path.basename(filename).split(".", 1)[0]
        configs[name] = Config(**yaml.load(f))
        exec(test_template.format(name=name))
