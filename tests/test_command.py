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

_marker = object()

class TestCommand:

    def test__init__(self):
        with pytest.raises(TypeError):
            Command(None)
        def foo():
            pass
        command1 = Command(foo)
        assert isinstance(command1, Command)
        assert command1.definition is foo
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
        assert command2.subcommands['bar'].definition is Foo.bar
        assert command2.subcommands['baz'].definition is Foo.baz

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
        factory = mocker.Mock(return_value=_marker)
        class TestCommand(Command):
            """Subclass for being able to patch methods"""
            pass
        @TestCommand
        def foo():
            pass
        mock_setup_arguments = mocker.patch.object(foo, 'setup_arguments')
        mock_setup_subparsers = mocker.patch.object(foo, 'setup_subparsers')
        assert foo.setup_parser(factory) is _marker
        mock_setup_arguments.assert_called_once_with(_marker)
        mock_setup_subparsers.assert_called_once_with(_marker)
        factory.assert_called_once_with()

        factory.reset_mock()
        foo.setup_parser(factory, 'foo')
        factory.assert_called_once_with('foo')

        # args, kwargs, name
        factory.reset_mock()
        foo.options['parser'] = (('bar', 'boo'), dict(baz=42, foo=1))
        foo.setup_parser(factory, 'foo')
        factory.assert_called_once_with('bar', 'boo', baz=42, foo=1)

        # alias
        factory.reset_mock()
        foo.options['alias'] = ['bar', '32', '99']
        foo.setup_parser(factory)
        factory.assert_called_once_with(
            'bar', 'boo', aliases=['bar', '32', '99'], baz=42, foo=1)

        # description
        factory.reset_mock()
        foo.definition.__doc__ = "__doc__ set"
        foo.setup_parser(factory)
        factory.assert_called_once_with(
            'bar', 'boo', aliases=['bar', '32', '99'], baz=42, foo=1,
            description="__doc__ set")

        factory.reset_mock()
        foo.options['parser'] = ((), dict(description="@parser set"))
        foo.setup_parser(factory)
        factory.assert_called_once_with(aliases=['bar', '32', '99'],
                                        description="@parser set")

    def test_setup_arguments(self):
        pass

    def test_setup_subcommands(self):
        pass
