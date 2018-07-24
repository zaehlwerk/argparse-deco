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

import pytest

from argparse_deco.command import Command
from argparse_deco.cli import CommandDecorator, default, CLI


_marker = object()

class TestCommandDecorator:

    def test__init__(self):
        def bogus():
            pass
        cmd_deco = CommandDecorator(bogus, single=23, subscriptable=99)
        assert cmd_deco.name == "bogus"
        assert cmd_deco.owner is "CLI"
        assert cmd_deco.cli_deco is bogus
        assert cmd_deco.single is 23
        assert cmd_deco.key_args is None
        assert cmd_deco.subscriptable is 99

    def test__repr__(self):
        @CommandDecorator
        def foo(bar: str, baz: int=23):
            pass
        assert repr(foo) == "<CommandDecorator CLI.foo(bar:str, baz:int=23)>"

    def test__set_name__(self):
        foo = CommandDecorator()
        assert foo.name is None
        assert foo.owner == "CLI"
        class A:
            bar = foo
        assert foo.name == "bar"
        assert foo.owner == "A"

    def test__getitem__(self):
        foo = CommandDecorator()
        with pytest.raises(TypeError):
            foo["bar"]

        foo = CommandDecorator(subscriptable=True)
        assert foo.key_args == None
        bar = foo['bar']
        assert isinstance(bar, CommandDecorator)
        for name in vars(foo):
            if name == 'key_args':
                assert bar.key_args == 'bar'
            else:
                assert getattr(foo, name) == getattr(bar, name)

    def test__call__(self, mocker):
        # cli_deco is None
        foo = CommandDecorator()
        assert foo.cli_deco is None
        assert foo(_marker) is foo
        assert foo.cli_deco is _marker

        # cli_deco is defined
        # test single == False
        foo.name = 'bogus'
        mock_cli_deco = mocker.patch.object(
            foo, 'cli_deco', return_value=_marker)
        @foo(23, 42, bar=3, baz=99)
        def bar():
            pass
        assert isinstance(bar, Command)
        assert bar.options['bogus'] == [_marker]
        mock_cli_deco.assert_called_once_with(23, 42, bar=3, baz=99)

        mock_cli_deco.reset_mock()
        foo.subscriptable = True
        foo.key_args = "keyz"
        assert foo("3", 7, buz=2)(bar) is bar
        assert bar.options['bogus'] == [_marker, _marker]
        mock_cli_deco.assert_called_once_with("keyz", "3", 7, buz=2)

        # Test single == True
        mock_cli_deco.reset_mock()
        foo.single = True
        foo.key_args = "keyz2"
        assert foo(33, 18, boo=3)(bar) is bar
        assert bar.options['bogus'] is _marker
        mock_cli_deco.assert_called_once_with("keyz2", 33, 18, boo=3)


def test_default():
    assert default(23, 47, foo=3, baz=112) == ((23, 47), dict(foo=3, baz=112))

class TestCLI:

    def test__new__(self, mocker):
        mock_cli_parser = mocker.patch.object(
            CLI, 'parser', return_value=_marker)
        mock_command = mocker.patch.object(
            Command, '__init__', return_value=None)
        assert CLI("foo") is _marker
        mock_cli_parser.assert_called_once_with("foo")
        mock_command.assert_not_called()

        def foo():
            pass

        mock_cli_parser.reset_mock()
        assert CLI(foo, foo=2) is _marker
        mock_cli_parser.assert_called_once_with(foo, foo=2)
        mock_command.assert_not_called()

        mock_cli_parser.reset_mock()
        assert CLI(foo, 3) is _marker
        mock_cli_parser.assert_called_once_with(foo, 3)
        mock_command.assert_not_called()

        mock_cli_parser.reset_mock()
        command = Command()
        mock_command.reset_mock()
        assert CLI(command) is command
        mock_command.assert_not_called()
        mock_cli_parser.assert_not_called()

        assert isinstance(CLI(foo), Command)
        mock_command.assert_called_once_with(foo)
        mock_cli_parser.assert_not_called()

        class Bar:
            pass
        mock_command.reset_mock()
        assert isinstance(CLI(Bar), Command)
        mock_command.assert_called_once_with(Bar)
        mock_cli_parser.assert_not_called()

    def test_parser(self):
        @CLI.parser(23, 3, foo=2, bar=77)
        def foo():
            pass
        assert isinstance(foo, Command)
        assert foo.options['parser'] == ((23, 3), dict(foo=2, bar=77))

    def test_group(self):
        @CLI.group('foo3', "bar3", "baz3")
        @CLI.group('foo', "bar", "baz")
        @CLI.group('foo2', "bar2", "baz2")
        def foo():
            pass
        assert isinstance(foo, Command)
        assert foo.options['group'] == [
            ('foo2', dict(title="bar2", description="baz2")),
            ('foo', dict(title="bar", description="baz")),
            ('foo3', dict(title="bar3", description="baz3")),
        ]

    def test_mutually_exclusive(self):
        @CLI.mutually_exclusive('foo')
        @CLI.mutually_exclusive('foo2', True)
        def foo():
            pass
        assert isinstance(foo, Command)
        assert foo.options['mutually_exclusive'] == [
            ('foo2', dict(required=True)),
            ('foo', dict(required=False)),
        ]

    def test_subparsers(self):
        @CLI.subparsers(23, 3, foo=2, bar=77)
        def foo():
            pass
        assert isinstance(foo, Command)
        assert foo.options['subparsers'] == ((23, 3), dict(foo=2, bar=77))

    def test_alias(self):
        @CLI.alias('foo')
        @CLI.alias('foo2')
        def foo():
            pass
        assert isinstance(foo, Command)
        assert foo.options['alias'] == ['foo2', 'foo']
