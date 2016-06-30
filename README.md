# cedar [![PyPI version](https://badge.fury.io/py/cedar.svg)](https://badge.fury.io/py/cedar) [![Build Status](https://travis-ci.org/Bogdanp/cedar.svg?branch=master)](https://travis-ci.org/Bogdanp/cedar) [![Coverage Status](https://coveralls.io/repos/github/Bogdanp/cedar/badge.svg?branch=master)](https://coveralls.io/github/Bogdanp/cedar?branch=master)

_This is alpha-level stuff._

Cedar is a small web service declaration language.  You declare your
service using this language and then use that declaration to generate
client and server code for a number of programming languages.

## Goals

* A single transport (http) and serialization format (json).
* Simple, consolidated tooling.  All functionality must live under
  this repository and must be distributed under one package.
* Aim to be an 85% solution.  Be the most simple thing that covers the
  widest array of use cases.  Never add complexity for the sake of
  covering fringe use cases.
* Generated source code must be idiomatic to the generated language.
* Generated source code must be human-readable.

## Installation

`pip3 install cedar`

## Languages

Cedar currently targets Elm (clients) and Go (servers) source code.

### Go

`cedar generate go --help`

#### Requirements

Generated Go code has no external dependencies, but it does require at
least Go version 1.6.

### Elm

`cedar generate elm --help`

#### Requirements

Generated Elm code currently requires Elm 0.17 and the following packages:

* [elm-community/json-extra][json-extra] 1.x
* [lukewestby/elm-http-builder][http-builder] 2.x


[json-extra]: http://package.elm-lang.org/packages/elm-community/json-extra/1.0.0/
[http-builder]: http://package.elm-lang.org/packages/lukewestby/elm-http-builder/2.0.0/

## The Cedar language

A Cedar specification consists of one or more toplevel declarations.
All toplevel declarations must be valid `enum`s, `union`s, `record`s
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

``` cedar
enum Status { Ready, Done, Failed }
```

Enums introduce new types (named after the enum) whose values are
constrained to the tags defined in the enum.  The tags inside an enum
are serialized as strings.  For example, a record attribute with the
type `Status` can contain one of the following JSON values: `"Ready"`,
`"Done"` and `"Failed"`.

### Unions

``` cedar
union Resource { Post, Comment }
```

Unions join multiple types under a single new type.

### Records

``` cedar
record Post {
  id Int
  title String
  content String
  publishedAt DateTime
}
```

### Functions

``` cedar
fn createPost(title String, content String, publishedAt DateTime?) Post
```

#### Editor support

* [cedar-mode][cedar-mode] for Emacs


[cedar-mode]: https://github.com/Bogdanp/cedar-mode
