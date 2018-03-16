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
"""compat.py: Legacy support for older Python versions."""

import sys

__all__ = ('Base',)

if sys.version_info >= (3, 6):
    # From Python 3.6 class attributes are always ordered.
    OrderedClassMeta = type
    Base = object

else:
    from collections import OrderedDict

    class OrderedClassMeta(type):
        @classmethod
        def __prepare__(mcls, name, bases, **kwds):
            return OrderedDict()

        def __new__(mcls, name, bases, ns, **kwds):
            return super().__new__(mcls, name, bases, dict(ns))

        def __init__(cls, name, bases, ns, **kwds):
            super().__init__(name, bases, ns)
            cls._ordered_namespace = OrderedDict()
            for base in bases:
                try:
                    cls._ordered_namespace.update(base._ordered_namespace)
                except AttributeError:
                    pass
            cls._ordered_namespace.update(ns)

    class Base(metaclass=OrderedClassMeta):
        pass
