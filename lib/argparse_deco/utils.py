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
#
"""argparse_deco/utils.py: some helpers"""


class ReadonlyAttribute:
    """decorator which does not allow overwriting of the attribute"""

    __slots__ = ('name', 'attr')

    def __init__(self, attr):
        self.attr = attr
        self.name = getattr(attr, '__name__', None)

    def __set_name__(self, owner: type, name: str):
        self.name = name

    def __repr__(self):
        return f"{type(self).__name__}[{self.attr!r}]"

    def __get__(self, inst, owner):
        if inst is None:
            return self
        try:
            return self.attr.__get__(inst, owner)
        except AttributeError:
            return self.attr

    def __set__(self, inst, value):
        raise AttributeError(
            f"'{inst}' object attribute '{self.name}' is read-only")

    def __delete__(self, inst):
        raise AttributeError(
            f"'{inst}' object attribute '{self.name}' is read-only")
