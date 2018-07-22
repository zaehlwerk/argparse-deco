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
"""arguments.py: store arguments in annotation"""

from .compat import HAS_PY37, PEP560Meta

__all__ = ('Arg', 'Group')

class Arg(metaclass=type if HAS_PY37 else PEP560Meta):
    """Stores argument's options in the annotation"""

    __slots__ = ('name_or_flags', 'kwargs',)

    def __init__(self, *name_or_flags, **kwargs):
        self.name_or_flags = name_or_flags
        self.kwargs = kwargs

    def __call__(self, *name_or_flags, **kwargs):
        if name_or_flags:
            self.name_or_flags = name_or_flags
        self.kwargs.update(kwargs)
        return self

    def __class_getitem__(cls, arg_type):
        return cls(arg_type=arg_type)

    def apply(self, parameter, func):
        # This function is still a bit hackish
        args = self.name_or_flags
        kwargs = self.kwargs
        arg_type = kwargs.pop('arg_type', None)
        if arg_type is bool:
            kwargs['action'] = 'store_true' if parameter.default \
                               else 'store_false'
        else:
            if parameter.default is not parameter.empty:
                kwargs['default'] = parameter.default
        if arg_type is not None and \
             not kwargs.get('action', '').startswith('store'):
            kwargs['type'] = arg_type
        kwargs['dest'] = parameter.name
        func(*args, **kwargs)


class Group(Arg):
    """Stores additionally the group association in the annotation"""

    __slots__ = ('group',)

    def __class_getitem__(cls, group: str, arg_type):
        arg = super().__class_getitem__(arg_type)
        arg.group = group
        return arg
