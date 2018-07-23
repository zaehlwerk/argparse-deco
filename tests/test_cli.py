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

from argparse_deco import cli
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
        assert cmd_deco.key_args == ()
        assert cmd_deco.subscriptable is 99

    def test__repr__(self):
        @CommandDecorator
        def foo(bar: str, baz: int=23):
            pass
        assert repr(foo) == "<CommandDecorator CLI.foo(bar:str, baz:int=23)>"


def test_default():
    assert default(23, 47, foo=3, baz=112) == ((23, 47), dict(foo=3, baz=112))

class TestCLI:

    # def test__new__(self, mocker):
    #     mock_command = mocker.patch.object(
    #         cli, 'Command', return_value=_marker)
    #     assert CLI("foo", 1) is _marker
    #     mock_command.assert_called_once_with("foo")

    def test_parser(self):
        @CLI.parser(23, 3, foo=2, bar=77)
        def foo():
            pass
        assert isinstance(foo, cli.Command)
        assert foo.options['parser'] == ((23, 3), dict(foo=2, bar=77))

    def test_group(self):
        @CLI.group('foo3', "bar3", "baz3")
        @CLI.group('foo', "bar", "baz")
        @CLI.group('foo2', "bar2", "baz2")
        def foo():
            pass
        assert isinstance(foo, cli.Command)
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
        assert isinstance(foo, cli.Command)
        assert foo.options['mutually_exclusive'] == [
            ('foo2', dict(required=True)),
            ('foo', dict(required=False)),
        ]

    def test_subparsers(self):
        @CLI.subparsers(23, 3, foo=2, bar=77)
        def foo():
            pass
        assert isinstance(foo, cli.Command)
        assert foo.options['subparsers'] == ((23, 3), dict(foo=2, bar=77))

    def test_alias(self):
        @CLI.alias('foo')
        @CLI.alias('foo2')
        def foo():
            pass
        assert isinstance(foo, cli.Command)
        assert foo.options['alias'] == ['foo2', 'foo']
