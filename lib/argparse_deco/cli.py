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
"""cli.py: Decorator based synctactic sugar for argparse"""

import functools
from typing import Union

from .command import Command


def cli_decorator(cli_deco=None, *, single=False):
    def wrapped_wrapper(deco):
        @functools.wraps(deco)
        def wrapper(*args, **kwargs):
            def decorator(command):
                if not isinstance(command, Command):
                    command = Command(command)
                if single:
                    command.options[deco.__name__] = deco(*args, **kwargs)
                else:
                    try:
                        option = command.options[deco.__name__]
                    except KeyError:
                        option = []
                        command.options[deco.__name__] = option
                    option.append(deco(*args, **kwargs))
                return command
            return decorator
        return wrapper
    if cli_deco is None:
        return wrapped_wrapper
    return wrapped_wrapper(cli_deco)


class CLI:

    def __new__(cls, command: Union[callable, type]):
        return Command(command)

    @staticmethod
    @cli_decorator(single=True)
    def parser(*args, **kwargs):
        # signature = inspect.signature(argparse.ArgumentParser)
        # return signature.bind(*args, **kwargs)
        return args, kwargs

    @staticmethod
    @cli_decorator
    def group(name: str, title: str=None, description: str=None):
        return name, dict(title=title, description=description)

    @staticmethod
    @cli_decorator
    def mutually_exclusive(name: str, required: bool=False):
        return name, dict(required=required)

    @staticmethod
    @cli_decorator(single=True)
    def subparsers(*args, **kwargs):
        return args, kwargs

    @staticmethod
    @cli_decorator
    def alias(name: str):
        return name
