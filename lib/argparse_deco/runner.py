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
"""runner.py: Helper class for running a command"""

import argparse
import inspect


class CommandRunner:

    parser: argparse.ArgumentParser
    _ns: argparse.Namespace

    def __init__(self, namespace, **kwargs):
        self._ns = namespace
        self.parser = namespace._parser
        vars(self).update(kwargs)

    def __call__(self):
        try:
            func = self._ns._func
        except AttributeError:
            return self.parser.print_usage()

        args = ()
        kwargs = {}
        for i, name in enumerate(inspect.signature(func).parameters):
            if i == 0 and name == 'self':
                args = (self,)
            elif name in vars(self._ns):
                kwargs[name] = getattr(self._ns, name)
            elif name in vars(self):
                kwargs[name] = getattr(self, name)
        return func(*args, **kwargs)
