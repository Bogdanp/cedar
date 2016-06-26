# cedar [![Build Status](https://travis-ci.org/Bogdanp/cedar.svg?branch=master)](https://travis-ci.org/Bogdanp/cedar) [![Coverage Status](https://coveralls.io/repos/github/Bogdanp/cedar/badge.svg?branch=master)](https://coveralls.io/github/Bogdanp/cedar?branch=master)

_This is alpha-level stuff._

Cedar is a small web service declaration language.  You write your
service spec using its declaration format and then you use that spec
to generate client and server boilerplate for a number of programming
languages.

## Installation

`pip3 install cedar`

## Languages

Cedar currently targets Elm (clients) and Go (servers) source code.

### Go

`cedar generate go --help`

### Elm

`cedar generate elm --help`

## The Cedar language

A Cedar specification consists of zero or more toplevel declarations.
All top level declarations must be valid `enum`s, `union`s, `record`s
or `fn`s.

### Example

``` cedar
enum Role { User, Mod, Admin }

record User {
  id Int
  email String
  role Role
}

fn getUsers() [User]
fn getUser(id Int) User?
fn deleteUser(id Int) Bool
```

### Types

There are 5 builtin types: `Bool`, `DateTime`, `Int`, `Float` and
`String`.

List types are declared using the `[t]` syntax (eg. `[String]`), dict
types are declared using the `{String: t}` syntax, and nullable types
are declared using the `t?` syntax.

### Enums

### Unions

### Records

### Functions

#### Editor support

* [cedar-mode][cedar-mode] for Emacs


[cedar-mode]: https://github.com/Bogdanp/cedar-mode
