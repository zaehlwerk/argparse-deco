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

>>> from argparse_deco import CLI, Arg, Flag

An an example for a simple CLI, one may use `CLI` as decorator for a
function in order to transform it:

>>> @CLI(prog="prog")
... def prog(
...         integers: Arg(metavar='N', nargs='+', type=int,
...                       help="an integerfor the accumulator"),
...         accumulate: Arg('--sum', action='store_const', const=sum,
...                         help="sum the integers (default: find the max)"
...                         )=max):
...     """Process some integers."""
...     print(accumulate(integers))

The decorator `CLI` transforms the function `prog` into an `Command`
instance. Effectively `prog` takes some command line argument like
`[ "1", "2", "4", "--sum" ]` as `cli_args` keyword, which is transformed
by the `argparse` module into arguments `integer` and `accumulate`
passed down to the original function `prog`:

>>> prog(["1", "2", "4", "--sum"])
7
>>> prog(["1", "2", "4"])
4

In order to obtain the `ArgumentParser` instance, `prog` has the class
method `setup_parser`:

>>> parser = prog.setup_parser()
>>> print(parser)
ArgumentParser(prog='prog', usage=None, description='Process some integers.', formatter_class=<class 'argparse.HelpFormatter'>, conflict_handler='error', add_help=True)
>>> parser.print_usage()
usage: prog [-h] [--sum] N [N ...]

>>> parser.print_help()
usage: prog [-h] [--sum] N [N ...]
<BLANKLINE>
Process some integers.
<BLANKLINE>
positional arguments:
  N           an integerfor the accumulator
<BLANKLINE>
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
`CLI.parser` decorator which accepts any argument `ArgumentParser`
would.


Groups
------

Arguments can be groupsed by using the `Group` instead of `Arg` in the
argument's annotation, which accepts a group name as first keyword and
the type as second one. The group can be customised (title,
description) using the `CLI.group` decorator:

>>> @CLI("prog")
... @CLI.group('foo', title="Foo", description="Foo group")
... def prog(
...         bar: Arg['foo'](help="Bar option"),
...         baz: Arg['foo'](help="Baz option")):
...     pass
>>> prog.setup_parser().print_help()
usage: prog [-h] bar baz
<BLANKLINE>
optional arguments:
  -h, --help  show this help message and exit
<BLANKLINE>
Foo:
  Foo group
<BLANKLINE>
  bar         Bar option
  baz         Baz option

Similarily using the `CLI.mutually_exclusive` decorator, arguments can
be turned into a mutually exclusive group.


Subcommands
===========

>>> @CLI("prog")
... @CLI.subparsers(help="sub-command help")
... class prog:
...     def __call__(foo: Flag('--foo', help="foo help")):
...         pass
...     def a(bar: Arg(type=int, help="bar help")):
...         """a help"""
...     def b(baz: Arg('--baz', choices='XYZ', help="baz help")):
...         """b help"""
>>> prog.parser.print_help()
usage: prog [-h] [--foo] {a,b} ...
<BLANKLINE>
positional arguments:
  {a,b}       sub-command help
<BLANKLINE>
optional arguments:
  -h, --help  show this help message and exit
  --foo       foo help

>>> prog.parser.parse_args(['a', '12'])
Namespace(_func=<function prog.a at 0x...>, _parser=..., bar=12, foo=False)
>>> prog.parser.parse_args(['--foo', 'b', '--baz', 'Z'])
Namespace(_func=<function prog.b at 0x...>, _parser=..., baz='Z', foo=True)

Deeper levels of subcommands can be generated using class definitions within:

>>> @CLI("prog")
... class prog:
...     class foo:
...         """foo subcommand"""
...         def bar():
...             """foo bar subsubcommand"""
...         def baz():
...             """foo baz subsubcommand"""
...     class oof:
...         def rab():
...             """oof rab subsubcommand"""
...         def zab():
...             """oof zab subsubcommand"""
>>> prog.parser.print_help()
usage: prog [-h] {foo,oof} ...
<BLANKLINE>
positional arguments:
  {foo,oof}
<BLANKLINE>
optional arguments:
  -h, --help  show this help message and exit

>>> prog.parser.parse_args(['foo', '-h'])
Traceback (most recent call last):
...
SystemExit: 0
