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
"""command.py: Wrapper class for parsing a definition"""

from collections.abc import MutableMapping
import argparse
import functools
import inspect
from typing import Any, List, Dict, Union, Tuple

from .arguments import Arg

class CommandRunner:

    parser: argparse.ArgumentParser
    ns: argparse.Namespace

    def __init__(self, namespace, **kwargs):
        self.ns = namespace
        self.parser = namespace._parser
        vars(self).update(kwargs)

    def __call__(self):
        try:
            func = self.ns._func
        except AttributeError:
            return self.parser.print_usage()

        args = ()
        kwargs = {}
        for i, name in enumerate(inspect.signature(func).parameters):
            if i == 0 and name == 'self':
                args = (self,)
            elif name in vars(self.ns):
                kwargs[name] = getattr(self.ns, name)
            elif name in vars(self):
                kwargs[name] = getattr(self, name)
        return func(*args, **kwargs)


class Command(MutableMapping):
    """Wraps a command (class or function) for creating
    an ArgumentParser instance. Additionally it can pass these
    ArgumentParser's arguments to the function (or the class'
    __call__ method) and execute it."""

    __slots__ = ('definition', 'options', 'subcommands')

    command: Union[callable, type]
    options: Dict[str, Any]
    # subcommands: Dict[str, Command]

    def __init__(self, definition: Union[callable, type]):
        if inspect.isclass(definition):
           self.definition = definition
        elif inspect.isfunction(definition):
           self.definition = type(
               definition.__name__, (), dict(
                   __doc__=definition.__doc__,
                   __module__=definition.__module__,
                   __qualname__=definition.__qualname__,
                   __call__=definition)
           )
        else:
            raise TypeError(
                f"{definition!r} is neither a class nor a function")

        self.options = dict()

        def subcommands():
            for name, attr in vars(definition).items():
                if not name.startswith('__'):
                    if isinstance(attr, Command):
                        yield name, attr
                    elif inspect.isfunction(attr) or inspect.isclass(attr):
                        yield name, Command(attr)
        self.subcommands = dict(subcommands())

    @property
    def name(self) -> str:
        return self.definition.__name__

    # Subcommand access by instance's keys
    def __getitem__(self, key: str):
        return self.subcommands[key]

    def __setitem__(self, key: str, command: Union[callable, type]):
        self.subcommands[key] = Command(command)

    def __delitem__(self, key: str):
        del self.subcommands[key]

    def __iter__(self):
        return iter(self.subcommands)

    def __len__(self):
        return len(self.subcommands)

    def subcommand(self, definition):
        """Decorator for adding a subcommand"""
        command = definition if isinstance(definition, Command) \
            else Command(definition)
        self.subcommands[definition.__name__] = command
        return command

    # Parsing
    def setup_parser(self, factory=argparse.ArgumentParser, name=None):
        """creates the ArgumentParser and calls setup_{arguments,subparsers}"""
        args, kwargs = self.options.get('parser', ((), {}))
        if not args and name:
            args = (name,)

        if 'alias' in self.options:
            kwargs['aliases'] = self.options['alias']
        if self.definition.__doc__:
            kwargs['description'] = kwargs.pop(
                'description', self.definition.__doc__)
        parser = factory(*args, **kwargs)
        parser.set_defaults(_parser=parser)
        self.setup_arguments(parser)
        self.setup_subparsers(parser)
        return parser

    def setup_arguments(self, parser):
        """process command's arguments"""
        function = self.definition.__call__

        groups = dict()
        for name, kwargs in reversed(self.options.get('group', ())):
            groups[name] = parser.add_argument_group(**kwargs)
        for name, kwargs in reversed(
                self.options.get('mutually_exclusive', ())):
            if name in groups:
                raise argparse.ArgumentError(
                    None, "A regular group cannot be mutually exclusive: "
                    f"{name}")
            groups[name] = parser.add_mutually_exclusive_group(**kwargs)
        for group_name, args, kwargs in reversed(
                self.options.get('argument', ())):
            if group_name:
                try:
                    group = groups[group_name]
                except KeyError:
                    group = parser.add_argument_group()
                    groups[group_name] = group
                group.add_argument(*args, **kwargs)
            else:
                parser.add_argument(*args, **kwargs)

        if inspect.isfunction(function):
            signature = inspect.signature(function)
            for name, parameter in signature.parameters.items():
                argument = parameter.annotation
                if isinstance(argument, Arg):
                    default = None if parameter.default is parameter.empty \
                              else parameter.default
                    try:
                        group = groups[argument.group]
                    except AttributeError:
                        argument.apply(parser, name, default)
                        continue
                    except KeyError:
                        group = parser.add_argument_group()
                        groups[argument.group] = group
                    argument.apply(group, name, default)

            # setup default action
            parser.set_defaults(_func=function)

    def setup_subparsers(self, parser):
        """process subparsers"""
        if 'subparsers' in self.options or self.subcommands:
            args, kwargs = self.options.get('subparsers', ((), {}))
            # kwargs['required'] = kwargs.pop(
            #     'required', not inspect.isfunction(self.definition.__call__))
            subparsers = parser.add_subparsers(*args, **kwargs)
            for name, command in self.subcommands.items():
                command.setup_parser(subparsers.add_parser, name)

    @property
    def parser(self):
        return self.setup_parser()

    def __call__(self, args: List[str]=None, **kwargs):
        """Parse `args` and run the fitting command.

        :params:
           args:     List of command line arguments for argument parser
           kwargs:   Additional keywords
        """
        Runner = self.options.get('command_runner', CommandRunner)
        return Runner(self.parser.parse_args(args), **kwargs)()
