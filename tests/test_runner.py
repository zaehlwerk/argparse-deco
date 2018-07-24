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

from argparse_deco.runner import CommandRunner

_marker = object()
_marker2 = object()


class TestRunner:

    def test__init__(self):
        class Namespace:
            _parser = _marker
        ns = Namespace()
        runner = CommandRunner(ns, foo=1, bar=3)
        assert runner._ns is ns
        assert runner.parser is _marker
        assert runner.foo is 1
        assert runner.bar is 3

    def test__call__(self, mocker):
        class Parser:
            def print_usage():
                pass
        mock_print_usage = mocker.patch.object(
            Parser, 'print_usage', return_value=_marker)
        parser = Parser()
        class Namespace:
            _parser = parser
        ns = Namespace()
        runner = CommandRunner(ns)
        assert runner() is _marker
        mock_print_usage.assert_called_once_with()

        # without self
        mock_print_usage.reset_mock()
        def foo(foo, bar, baz=43, zoo=2, blub=99):
            return (foo, bar, baz, zoo, blub)
        ns._func = foo
        ns.foo = 22
        ns.zoo = 3
        runner = CommandRunner(ns, bar=47, baz=4)
        assert runner() == (22, 47, 4, 3, 99)
        mock_print_usage.assert_not_called()

        # with self
        def foo(self, foo, bar, baz=43, zoo=2, blub=99):
            return (self, foo, bar, baz, zoo, blub)
        ns._func = foo
        ns.foo = 22
        ns.zoo = 3
        runner = CommandRunner(ns, bar=47, baz=4)
        assert runner() == (runner, 22, 47, 4, 3, 99)
