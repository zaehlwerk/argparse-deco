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

import inspect
from typing import Type

from .command import Command

class CommandDecorator:

    def __init__(self, cli_deco: callable=None, *, single: bool=False):
        if cli_deco is None:
            self.name = None
        else:
            self.name = cli_deco.__name__
        self.owner = "CLI"
        self.cli_deco = cli_deco
        self.single = single

    def __repr__(self):
        try:
            signature = inspect.signature(self.cli_deco)
        except TypeError:
            signature = "(...)"
        return f"<CommandDecorator {self.owner}.{self.name}{signature}>"

    def __set_name__(self, owner, name: str):
        self.owner = owner.__name__
        self.name = name

    def __call__(self, *args, **kwargs):
        if self.cli_deco is None:
            self.cli_deco = args[0]
            return self

        def decorator(command):
            if not isinstance(command, Command):
                command = Command(command)
            if self.single:
                command.options[self.name] = self.cli_deco(*args, **kwargs)
            else:
                try:
                    option = command.options[self.name]
                except KeyError:
                    option = []
                    command.options[self.name] = option
                option.append(self.cli_deco(*args, **kwargs))
            return command
        return decorator


def default(*args, **kwargs):
    return args, kwargs


class CLI:

    def __new__(cls, *args, **kwargs):
        if len(args) == 1 and not kwargs:
            if isinstance(args[0], Command):
                return args[0]
            if inspect.isclass(args[0]) or inspect.isfunction(args[0]):
                return Command(args[0])
        return cls.parser(*args, **kwargs)

    parser = CommandDecorator(default, single=True)
    subparsers = CommandDecorator(default, single=True)

    @CommandDecorator(single=True)
    def bind(executor_class: type):
        return executor_class

    @CommandDecorator
    def argument(*args, group=None, **kwargs):
        return group, args, kwargs

    @CommandDecorator
    def group(name: str, title: str=None, description: str=None):
        return name, dict(title=title, description=description)

    @CommandDecorator
    def mutually_exclusive(name: str, required: bool=False):
        return name, dict(required=required)

    @CommandDecorator
    def alias(name: str):
        return name
