=============
argparse-deco
=============

argparse-deco is basically syntatic sugar for argparse using
decorators. Although it inherited some ideas and concepts from
Kevin L. Mitchell's **cli_tools**
(https://github.com/klmitch/cli_tools), it does not share its source
code.

Its main difference is the possibility to abuse Python's class
syntax to define complex CLI tools with nested subcommands.

Simple CLI
==========

The API suffices to use three imports.

>>> from argparse_deco import Cli, Arg, Group

An an example for a simple CLI, one may use `Cli` as decorator for a
function in order to transform it:

>>> @Cli
... def prog(
...         integers: Arg[int](metavar='N', nargs='+',
...                            help="an integerfor the accumulator"),
...         accumulate: Arg('--sum', action='store_const', const=sum,
...                         help="sum the integers (default: find the max)"
...                         )=max):
...     """Process some integers."""
...     print(accumulate(integers))

The decorator `Cli` transforms the function `prog` into a `CliMeta`
type class having `prog` as its `__call__` method. Effectively `prog`
takes some command line argument like `[ "1", "2", "4", "--sum" ]` as
single argument, which is transformed by the `argparse` module into
arguments `integer` and `accumulate` passed down to the original
function `prog`:

>>> prog(["1", "2", "4", "--sum"])
7
>>> prog(["1", "2", "4"])
4

In order to obtain the `ArgumentParser` instance, `prog` has the class
method `get_parser`:

>>> parser = prog.get_parser()
>>> print(parser)
ArgumentParser(prog='prog', usage=None, description='Process some integers.', formatter_class=<class 'argparse.HelpFormatter'>, conflict_handler='error', add_help=True)
>>> parser.print_usage()
usage: prog [-h] [--sum] N [N ...]

>>> parser.print_help()
usage: prog [-h] [--sum] N [N ...]

Process some integers.

positional arguments:
  N           an integerfor the accumulator

optional arguments:
  -h, --help  show this help message and exit
  --sum       sum the integers (default: find the max)


Arguments
---------

In order for a function's arguments to be processed as
`ArgumentParser` argument, they have to annotated by `Arg`. Basically
`Arg` allows a the type as keyword, and arbitrary keyword arguments
which are passed almost unchanged to `ArgumentParser.add_argument`.


Parser
------

While the `ArgumentParser` instance's `description` is usually the
function's docstring, one may want to further customise it using the
`Cli.parser` decorator which accepts any argument `ArgumentParser`
would.


Groups
------

Arguments can be groupsed by using the `Group` instead of `Arg` in the
argument's annotation, which accepts a group name as first keyword and
the type as second one. The group can be customised (title,
description) using the `Cli.group` decorator:

>>> @Cli.group('foo', title="Foo", description="Foo group")
... def prog(
...         bar: Group['foo', str](help="Bar option"),
...         baz: Group['foo', int](help="Baz option")):
...     pass
>>> prog.get_parser().print_help()
usage: prog [-h] bar baz

optional arguments:
  -h, --help  show this help message and exit

Foo:
  Foo group

  bar         Bar option
  baz         Baz option

Similarily using the `Cli.mutually_exclusive` decorator, arguments can
be turned into a mutually exclusive group.


Subcommands
===========

