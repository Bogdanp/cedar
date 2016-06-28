import os
import re

from setuptools import find_packages, setup


def rel(*xs):
    return os.path.join(os.path.abspath(os.path.dirname(__file__)), *xs)


def read_requirements(filename):
    with open(filename, "r") as f:
        for line in f.readlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            if line.startswith("-r"):
                yield from read_requirements(line[3:])

            else:
                yield line


def read_version(filename):
    with open(filename, "r") as f:
        contents = f.read()
        return re.search(r'^__version__ = "([^"]+)"$', contents, re.MULTILINE).group(1)


version = read_version(rel("cedar", "__init__.py"))
install_requires = list(read_requirements(rel("requirements.txt")))
tests_require = list(read_requirements(rel("requirements_dev.txt")))

setup(
    name="cedar",
    version=version,
    entry_points={
        "console_scripts": {
            "cedar = cedar.cli:main"
        }
    },
    packages=find_packages(),
    install_requires=install_requires,
    tests_require=tests_require,
    description="A web service definition format and source code generator.",
    long_description="See https://github.com/Bogdanp/cedar",
    author="Bogdan Popa",
    author_email="popa.bogdanp@gmail.com",
    url="https://github.com/Bogdanp/cedar",
    license="BSD3",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Natural Language :: English",
        "License :: OSI Approved :: BSD License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.5",
    ]
)
