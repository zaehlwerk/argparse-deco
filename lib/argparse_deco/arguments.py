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

__all__ = ('Arg', 'Flag', 'Append', 'Count')


class Arg(metaclass=type if HAS_PY37 else PEP560Meta):
    """Stores argument's options in the annotation"""

    __slots__ = ('name_or_flags', 'kwargs', 'group')

    def __class_getitem__(cls, group):
        """assigns argument to a group"""
        arg = cls()
        arg.group = group
        return arg

    def __init__(self, *name_or_flags, **kwargs):
        self.name_or_flags = name_or_flags
        self.kwargs = kwargs
        self.group = None

    def __call__(self, *name_or_flags, **kwargs):
        if name_or_flags:
            self.name_or_flags = name_or_flags
        self.kwargs.update(kwargs)
        return self

    def __repr__(self) -> str:
        group = f"[{self.group!r}]" if self.group else ""

        def args():
            for s in self.name_or_flags:
                yield repr(s)
            for k, v in self.kwargs.items():
                yield f"{k}={v}"
        return f"{type(self).__name__}{group}({', '.join(args())})"

    def apply(self, parser, name: str, default=None) -> None:
        args = self.name_or_flags
        kwargs = self.kwargs
        kwargs['dest'] = name
        if default:
            kwargs['default'] = default
        parser.add_argument(*args, **kwargs)


class Flag(Arg):
    """Flag argument"""

    def apply(self, parser, name: str, default=None) -> None:
        args = self.name_or_flags
        kwargs = self.kwargs
        kwargs['dest'] = name
        kwargs['action'] = 'store_true' if default in (False, None) \
                           else 'store_false'
        kwargs['default'] = bool(default)
        parser.add_argument(*args, **kwargs)


class Append(Arg):

    def apply(self, parser, name: str, default=None) -> None:
        args = self.name_or_flags
        kwargs = self.kwargs
        kwargs['dest'] = name
        kwargs['action'] = 'append'
        parser.add_argument(*args, **kwargs)


class Count(Arg):
    """Count flags"""

    def apply(self, parser, name: str, default=None) -> None:
        args = self.name_or_flags
        kwargs = self.kwargs
        kwargs['action'] = 'count'
        kwargs['dest'] = name
        parser.add_argument(*args, **kwargs)
