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

import inspect

import pytest

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
        assert command1.subcommands == {}

        class Foo:
            def bar():
                pass
            def baz():
                pass
        command2 = Command(Foo)
        assert isinstance(command2, Command)
        assert command2.definition is Foo
        assert command2.options == {}
        assert tuple(command2.subcommands.keys()) == ('bar', 'baz')
        assert all(isinstance(sc, Command)
                   for sc in command2.subcommands.values())
        assert command2.subcommands['bar'].definition.__call__ is Foo.bar
        assert command2.subcommands['baz'].definition.__call__ is Foo.baz

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
        assert Foo.subcommands == dict()
        subcmd = Foo.subcommand(bar)
        assert isinstance(subcmd, Command)
        assert Foo.subcommands == dict(bar=subcmd)

    def test_setup_parser(self, mocker):
        class TestParser:
            def __init__(self, *args, **kwargs):
                pass
            def set_defaults(self, **kwargs):
                pass
        mock_parser = mocker.patch.object(
            TestParser, '__init__', return_value=None)
        mock_set_defaults = mocker.patch.object(
            TestParser, 'set_defaults')
        class TestCommand(Command):
            """Subclass for being able to patch methods"""
            pass
        @TestCommand
        def foo():
            pass
        mock_setup_arguments = mocker.patch.object(foo, 'setup_arguments')
        mock_setup_subparsers = mocker.patch.object(foo, 'setup_subparsers')
        parser = foo.setup_parser(TestParser)
        assert isinstance(parser, TestParser)
        mock_parser.assert_called_once_with()
        mock_setup_arguments.assert_called_once_with(parser)
        mock_setup_subparsers.assert_called_once_with(parser)
        mock_set_defaults.assert_called_once_with(_parser=parser)

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
