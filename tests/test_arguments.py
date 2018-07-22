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

from argparse_deco.arguments import Arg, Flag


_marker = object()


class TestArg:

    def test__class_item__(self):
        arg = Arg[_marker]
        assert isinstance(arg, Arg)
        assert arg.group is _marker

    def test__init__(self):
        arg = Arg(34, 23, foo=21, bar=100)
        assert arg.name_or_flags == (34, 23)
        assert arg.kwargs == dict(foo=21, bar=100)

    def test__call__(self):
        arg = Arg(34, 23, foo=21, bar=100)
        assert arg(3, 7, bar=3, baz=10) is arg
        assert arg.name_or_flags == (3, 7)
        assert arg.kwargs == dict(foo=21, bar=3, baz=10)

    def test__repr__(self):
        arg = Arg(34, 23, foo=21, bar=100)
        assert repr(arg) == "Arg(34, 23, foo=21, bar=100)"
        assert repr(Arg['foo']) == "Arg['foo']()"

    def test_apply(self, mocker):
        class Parser:
            def add_argument(self, *args, **kwargs):
                pass
        parser = Parser()
        mock_add_argument = mocker.patch.object(parser, 'add_argument')
        arg = Arg(34, 23, foo=21, bar=100)
        arg.apply(parser, 'bogus')
        mock_add_argument.assert_called_once_with(
            34, 23, foo=21, bar=100, dest='bogus')
        mock_add_argument.reset_mock()
        arg.apply(parser, 'bogus', _marker)
        mock_add_argument.assert_called_once_with(
            34, 23, foo=21, bar=100, dest='bogus', default=_marker)
