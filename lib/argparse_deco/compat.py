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


HAS_PY37 = sys.version_info >= (3, 7)


class PEP560Meta(type):

    def __new__(mcls, name, bases, ns, **kwargs):
        if '__class_getitem__' in ns:
            ns['__class_getitem__'] = classmethod(ns['__class_getitem__'])
        return super().__new__(mcls, name, bases, ns, **kwargs)

    def __getitem__(cls, args):
        return cls.__class_getitem__(args)
