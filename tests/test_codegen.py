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


class Config(namedtuple("Config", "dir endpoint targets commands entrypoint cases")):
    def test(self, capsys):
        self._build_targets(capsys)
        proc = self._run_commands()

        try:
            self._run_cases()
        finally:
            proc.terminate()

    def _build_targets(self, capsys):
        for target in self.targets:
            command = shlex.split(target["cmd"]) + [rel(target["in"])]
            filename = target["out"]

            with open(rel(filename), "w") as f, arguments(*command):
                cli.main()
                output, _ = capsys.readouterr()
                f.write(output)

    def _run_commands(self):
        popen = partial(Popen, cwd=rel(self.dir))
        for command in self.commands:
            assert popen(shlex.split(command)).wait() == 0

        proc = popen(shlex.split(self.entrypoint), stdout=PIPE, stderr=STDOUT)
        while True:
            line = proc.stdout.readline()
            if b"listening" in line.lower():
                return proc

    def _run_cases(self):
        for case in self.cases:
            print("Running test case: {!r}".format(case.get("description", "")))

            request = case["request"]
            expected_response = case["response"]
            response = requests.post(
                self.endpoint,
                params={"fn": request["fn"]},
                data=json.dumps(request["data"])
            )

            if "code" in expected_response:
                assert expected_response["code"] == response.status_code

            if "data" in expected_response:
                assert expected_response["data"] == response.json()


configs = {}
for i, filename in enumerate(iglob(rel("*.yaml"))):
    with open(filename) as f:
        name = os.path.basename(filename).split(".", 1)[0]
        configs[i] = Config(**yaml.load(f))
        exec("""\
def test_{name}(capsys):
  configs[{i}].test(capsys)
""".format(name=name, i=i))
