# -*- coding: utf-8 -*-
#
# Copyright (C) 2018 by Gregor Giesen
#
# This file is part of argparse-deco.
#
# argparse-deco is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published
# by the Free Software Foundation, either version 3 of the License,
# or (at your option) any later version.
#
# argparse-deco is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with argparse-deco. If not, see <http://www.gnu.org/licenses/>.

import argparse
import inspect

import pytest

from argparse_deco.arguments import Arg
from argparse_deco.command import Command

_marker = object()
_marker2 = object()


class TestCommand:

    def test__init__(self):
        with pytest.raises(TypeError):
            Command(None)
        def foo():
            """bogus doc"""
            pass
        command1 = Command(foo)
        assert isinstance(command1, Command)
        assert inspect.isclass(command1.definition)
        assert command1.definition.__call__ is foo
        assert command1.definition.__doc__ is foo.__doc__
        assert command1.definition.__module__ is foo.__module__
        assert command1.definition.__qualname__ is foo.__qualname__
        assert command1.options == {}
        assert command1.parent is None
        assert command1.subcommands == {}

        class Foo:
            def bar():
                pass
            def baz():
                pass
            @Command
            def zoo():
                pass
        command2 = Command(Foo, _marker)
        assert isinstance(command2, Command)
        assert command2.definition is Foo
        assert command2.options == {}
        assert command2.parent is _marker
        assert tuple(command2.subcommands.keys()) == ('bar', 'baz', 'zoo')
        assert all(isinstance(sc, Command)
                   for sc in command2.subcommands.values())
        assert command2.subcommands['bar'].definition.__call__ is Foo.bar
        assert command2.subcommands['baz'].definition.__call__ is Foo.baz
        assert command2.subcommands['zoo'].parent is command2

    def test_name(self):
        def foo():
            pass
        assert Command(foo).name == 'foo'

    def test_subcommand(self):
        @Command
        class Foo:
            pass
        def bar():
            pass
        @Command
        def baz():
            pass
        assert Foo.subcommands == dict()
        subcmd1 = Foo.subcommand(bar)
        subcmd2 = Foo.subcommand(baz)
        assert isinstance(subcmd1, Command)
        assert isinstance(subcmd2, Command)
        assert baz.parent is Foo
        assert Foo.subcommands == dict(bar=subcmd1, baz=baz)

    def test_setup_parser(self, mocker):
        class TestParser:
            def __init__(self, *args, **kwargs):
                pass
            def add_argument_group(self, **kwargs):
                pass
            def add_argument(self, *args, **kwargs):
                pass
            def set_defaults(self, **kwargs):
                pass
        mock_parser = mocker.patch.object(
            TestParser, '__init__', return_value=None)
        mock_add_argument = mocker.patch.object(
            TestParser, 'add_argument')
        mock_add_argument_group = mocker.patch.object(
            TestParser, 'add_argument_group', return_value=_marker)
        mock_set_defaults = mocker.patch.object(
            TestParser, 'set_defaults')
        class TestCommand(Command):
            """Subclass for being able to patch methods"""
            pass
        @TestCommand
        def foo():
            pass

        mock_setup_arguments = mocker.patch.object(
            foo, 'setup_arguments', return_value=iter(()))
        mock_setup_deco_groups = mocker.patch.object(
            foo, 'setup_deco_groups', return_value=())
        mock_setup_subparsers = mocker.patch.object(foo, 'setup_subparsers')
        parser = foo.setup_parser(TestParser)
        assert isinstance(parser, TestParser)
        mock_parser.assert_called_once_with()
        mock_setup_arguments.assert_called_once_with()
        mock_setup_deco_groups.assert_called_once_with(parser)
        mock_setup_subparsers.assert_called_once_with(parser)
        mock_set_defaults.assert_called_once_with(_parser=parser)
        mock_add_argument.assert_not_called()
        mock_add_argument_group.assert_not_called()

        mock_parser.reset_mock()
        foo.setup_parser(TestParser, 'foo')
        mock_parser.assert_called_once_with('foo')

        # args, kwargs, name
        mock_parser.reset_mock()
        foo.options['parser'] = (('bar', 'boo'), dict(baz=42, foo=1))
        foo.setup_parser(TestParser, 'foo')
        mock_parser.assert_called_once_with('bar', 'boo', baz=42, foo=1)

        # alias
        mock_parser.reset_mock()
        foo.options['alias'] = ['bar', '32', '99']
        foo.setup_parser(TestParser)
        mock_parser.assert_called_once_with(
            'bar', 'boo', aliases=['bar', '32', '99'], baz=42, foo=1)

        # description
        mock_parser.reset_mock()
        foo.definition.__doc__ = "__doc__ set"
        foo.setup_parser(TestParser)
        mock_parser.assert_called_once_with(
            'bar', 'boo', aliases=['bar', '32', '99'], baz=42, foo=1,
            description="__doc__ set")

        mock_parser.reset_mock()
        foo.options['parser'] = ((), dict(description="@parser set"))
        foo.setup_parser(TestParser)
        mock_parser.assert_called_once_with(aliases=['bar', '32', '99'],
                                            description="@parser set")

        # help
        mock_parser.reset_mock()
        foo.parent = True
        foo.setup_parser(TestParser)
        mock_parser.assert_called_once_with(aliases=['bar', '32', '99'],
                                            description="@parser set",
                                            help="__doc__ set")

        mock_parser.reset_mock()
        foo.options['parser'] = ((), dict(help="@parser set"))
        foo.setup_parser(TestParser)
        mock_parser.assert_called_once_with(aliases=['bar', '32', '99'],
                                            description="__doc__ set",
                                            help="@parser set")

        mock_setup_deco_groups = mocker.patch.object(
            foo, 'setup_deco_groups', return_value=(
                ('foo', 'foo_group'),
                ('bar', 'bar_group')
            ))
        def setup_arguments():
            parser = yield
            assert isinstance(parser, TestParser)
            parser = yield 'foo'
            assert parser == 'foo_group'
            parser = yield 'bar'
            assert parser == 'bar_group'
            parser = yield 'bogus'
            assert parser is _marker
            parser = yield 'bogus'
            assert parser is _marker
        foo.setup_arguments = setup_arguments
        foo.setup_parser(TestParser)
        mock_add_argument_group.assert_called_once_with('bogus')

    def test_setup_deco_groups(self, mocker):
        class TestParser:
            def add_argument_group(self, **kwargs):
                pass
            def add_mutually_exclusive_group(self, **kwargs):
                pass
        mock_add_argument_group = mocker.patch.object(
            TestParser, 'add_argument_group')
        mock_add_mutually_exclusive_group = mocker.patch.object(
            TestParser, 'add_mutually_exclusive_group')
        parser = TestParser()

        class TestCommand(Command):
            """Subclass for being able to patch methods"""
            pass
        @TestCommand
        def foo():
            pass

        # test groups
        foo.options['group'] = [('foo', dict(bar=2, baz=3)),
                                ('bar', dict(foo=3, zoo=12))]
        foo.options['mutually_exclusive'] = [('zoo', dict(foo=13)),
                                             ('ooz', dict(zoo=1))]
        gen = foo.setup_deco_groups(parser)

        name, group = next(gen)
        assert name == 'bar'
        mock_add_argument_group.assert_called_once_with(foo=3, zoo=12)
        mock_add_mutually_exclusive_group.assert_not_called()

        mock_add_argument_group.reset_mock()
        mock_add_mutually_exclusive_group.reset_mock()
        name, group = next(gen)
        assert name == 'foo'
        mock_add_argument_group.assert_called_once_with(bar=2, baz=3)
        mock_add_mutually_exclusive_group.assert_not_called()

        mock_add_argument_group.reset_mock()
        mock_add_mutually_exclusive_group.reset_mock()
        name, group = next(gen)
        assert name == 'ooz'
        mock_add_argument_group.assert_not_called()
        mock_add_mutually_exclusive_group.assert_called_once_with(zoo=1)

        mock_add_argument_group.reset_mock()
        mock_add_mutually_exclusive_group.reset_mock()
        name, group = next(gen)
        assert name == 'zoo'
        mock_add_argument_group.assert_not_called()
        mock_add_mutually_exclusive_group.assert_called_once_with(foo=13)

        with pytest.raises(StopIteration):
            next(gen)

        # check conflicting group names
        foo.options['group'] = [('foo', dict(bar=2, baz=3))]
        foo.options['mutually_exclusive'] = [('foo', dict(foo=13))]
        gen = foo.setup_deco_groups(parser)
        assert next(gen)[0] == 'foo'
        mock_add_argument_group.reset_mock()
        mock_add_mutually_exclusive_group.reset_mock()
        with pytest.raises(argparse.ArgumentError):
            name, group = next(gen)
        mock_add_argument_group.assert_not_called()
        mock_add_mutually_exclusive_group.assert_not_called()

    def test_setup_arugments(self, mocker):
        class TestParser:
            def add_argument(self, *args, **kwargs):
                pass
            def set_defaults(self, **kwargs):
                pass
        mock_add_argument = mocker.patch.object(
            TestParser, 'add_argument')
        mock_set_defaults = mocker.patch.object(
            TestParser, 'set_defaults')
        parser = TestParser()
        class TestCommand(Command):
            """Subclass for being able to patch methods"""
            pass
        @TestCommand
        def foo(a, b: Arg(), c: Arg['g2'], d: Arg['g3']=_marker):
            pass
        mock_argument_apply = mocker.patch.object(
            Arg, 'apply')

        foo.options['argument'] = [(None, (1,1), dict(foo=1, bar=1)),
                                   ('g1', (1,2), dict(foo=1, bar=2)),
                                   ('g2', (1,3), dict(foo=1, bar=3))]
        gen = foo.setup_arguments()
        assert next(gen) == 'g2'

        assert gen.send(parser) == 'g1'
        mock_add_argument.assert_called_once_with(1, 3, foo=1, bar=3)

        mock_add_argument.reset_mock()
        assert gen.send(parser) is None
        mock_add_argument.assert_called_once_with(1, 2, foo=1, bar=2)

        mock_add_argument.reset_mock()
        assert gen.send(parser) is None
        mock_add_argument.assert_called_once_with(1, 1, foo=1, bar=1)

        mock_add_argument.reset_mock()
        assert gen.send(parser) == 'g2'
        mock_add_argument.assert_not_called()
        mock_argument_apply.assert_called_once_with(parser, 'b', None)

        mock_argument_apply.reset_mock()
        assert gen.send(parser) == 'g3'
        mock_argument_apply.assert_called_once_with(parser, 'c', None)

        mock_argument_apply.reset_mock()
        assert gen.send(parser) is None
        mock_argument_apply.assert_called_once_with(parser, 'd', _marker)

        with pytest.raises(StopIteration):
            gen.send(parser)
        mock_set_defaults.assert_called_once_with(_func=foo.definition.__call__)

        # check case if foo.defininion.__call__ is not a function
        mock_argument_apply.reset_mock()
        mock_add_argument.reset_mock()
        mock_set_defaults.reset_mock()
        @TestCommand
        class foo:
            pass
        foo.options['argument'] = [('g4', (4,1), dict(foo=4, bar=1))]
        gen = foo.setup_arguments()
        assert next(gen) == 'g4'

        with pytest.raises(StopIteration):
            assert gen.send(parser) is None
        mock_add_argument.assert_called_once_with(4, 1, foo=4, bar=1)
        mock_set_defaults.assert_not_called()

    def test_setup_subparsers(self, mocker):
        class TestParser:
            def add_subparsers(self, *args, **kwargs):
                pass
        mock_add_subparsers = mocker.patch.object(
            TestParser, 'add_subparsers')
        parser = TestParser()
        class TestCommand(Command):
            """Subclass for being able to patch methods"""
            def setup_parser(self, func, name):
                pass
        @TestCommand
        def foo():
            pass

        # no 'subparsers'
        assert foo.setup_subparsers(parser) is None
        mock_add_subparsers.assert_not_called()

        # subparsers options
        foo.options['subparsers'] = (('foo', 'bar'), dict(baz=23, zoo=2))
        assert foo.setup_subparsers(parser) is None
        mock_add_subparsers.assert_called_once_with(
            'foo', 'bar', baz=23, zoo=2)

        # add subcommands
        mock_add_subparsers.reset_mock()
        del foo.options['subparsers']
        command1 = TestCommand(lambda: None)
        mock_setup_parser1 = mocker.patch.object(
            command1, 'setup_parser')
        command2 = TestCommand(lambda: None)
        mock_setup_parser2 = mocker.patch.object(
            command2, 'setup_parser')
        foo.subcommands['command1'] = command1
        foo.subcommands['command2'] = command2
        assert foo.setup_subparsers(parser) is None
        mock_add_subparsers.assert_called_once_with()
        mock_setup_parser1.assert_called_with(
            mock_add_subparsers.return_value.add_parser, 'command1')
        mock_setup_parser2.assert_called_with(
            mock_add_subparsers.return_value.add_parser, 'command2')

    def test_parser(self, mocker):
        def foo():
            pass
        mock_parser = mocker.patch.object(
            Command, 'setup_parser', return_value=_marker)
        command = Command(foo)
        assert command.parser is _marker
        mock_parser.assert_called_once_with()

    def test__call__(self, mocker):
        class Parser:
            def parse_args():
                pass
        mock_parse_args = mocker.patch.object(
            Parser, 'parse_args', return_value=_marker)
        parser = Parser()
        mock_setup_parser = mocker.patch.object(
            Command, 'setup_parser', return_value=parser)
        class Runner:
            pass
        mock_runner = mocker.patch.object(
            Runner, '__init__', return_value=None)
        mock_runner_call = mocker.patch.object(
            Runner, '__call__', return_value=_marker2)

        # without arguments
        @Command
        def foo():
            pass
        foo.options['command_runner'] = Runner
        assert foo() is _marker2
        mock_runner.assert_called_once_with(_marker)
        mock_runner_call.assert_called_once_with()
        mock_parse_args.assert_called_once_with(None)

        mock_runner.reset_mock()
        mock_runner_call.reset_mock()
        mock_parse_args.reset_mock()
        assert foo(['bogus', 'bar'], foo=32, bar=1) is _marker2
        mock_runner.assert_called_once_with(_marker, foo=32, bar=1)
        mock_runner_call.assert_called_once_with()
        mock_parse_args.assert_called_once_with(['bogus', 'bar'])
