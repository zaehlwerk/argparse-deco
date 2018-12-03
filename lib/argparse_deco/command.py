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

import argparse
import inspect
from typing import Any, List, Dict, Union

from .arguments import Arg

class Command:
    """Wraps a command (class or function) for creating
    an ArgumentParser instance. Additionally it can pass these
    ArgumentParser's arguments to the function (or the class'
    __call__ method) and execute it."""

    __slots__ = ('definition', 'options', 'parent', 'subcommands')

    # definition: type
    options: Dict[str, Any]
    # parent: Command
    # subcommands: Dict[str, Command]

    def __init__(self, definition: Union[callable, type], parent=None):
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
        self.parent = parent

        def subcommands():
            for name, attr in vars(definition).items():
                if not name.startswith('__'):
                    if isinstance(attr, Command):
                        attr.parent = self
                        yield name, attr
                    elif inspect.isfunction(attr) or inspect.isclass(attr):
                        yield name, Command(attr, self)
        self.subcommands = dict(subcommands())

    @property
    def name(self) -> str:
        return self.definition.__name__

    def subcommand(self, definition):
        """Decorator for adding a subcommand"""
        if isinstance(definition, Command):
            subcommand = definition
            subcommand.parent = self
        else:
            subcommand = Command(definition, self)
        self.subcommands[subcommand.definition.__name__] = subcommand
        return subcommand

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
            if self.parent:
                kwargs['help'] = kwargs.pop(
                    'help', self.definition.__doc__)
        parser = factory(*args, **kwargs)
        parser.set_defaults(_parser=parser)

        groups = dict(self.setup_deco_groups(parser))
        gen = self.setup_arguments()
        try:
            group_name = next(gen)
        except StopIteration:
            pass
        else:
            while True:
                if group_name is None:
                    arg_parser = parser
                elif group_name in groups:
                    arg_parser = groups[group_name]
                else:
                    arg_parser = parser.add_argument_group(group_name)
                    groups[group_name] = arg_parser

                try:
                    group_name = gen.send(arg_parser)
                except StopIteration:
                    break

        self.setup_subparsers(parser)
        return parser

    def setup_deco_groups(self, parser):
        """Setup argument groups defined by `CLI.group`
        and `CLI.mutually_exclusive`"""
        group_names = set()
        for name, kwargs in reversed(self.options.get('group', ())):
            group_names.add(name)
            yield name, parser.add_argument_group(**kwargs)
        for name, kwargs in reversed(
                self.options.get('mutually_exclusive', ())):
            if name in group_names:
                raise argparse.ArgumentError(
                    None, "A regular group cannot be mutually exclusive: "
                    f"{name}")
            yield name, parser.add_mutually_exclusive_group(**kwargs)

    def setup_arguments(self):
        """process command's arguments"""

        # setup decorator defined arguments
        for group_name, args, kwargs in reversed(
                self.options.get('argument', ())):
            parser = yield group_name
            parser.add_argument(*args, **kwargs)

        # setup signature defined arguments
        func = self.definition.__call__
        if inspect.isfunction(func):
            signature = inspect.signature(func)
            for name, parameter in signature.parameters.items():
                argument = parameter.annotation
                if isinstance(argument, Arg):
                    default = None if parameter.default is parameter.empty \
                              else parameter.default
                    parser = yield argument.group
                    argument.apply(parser, name, default)

            # setup default action
            parser = yield
            parser.set_defaults(_func=func)

    def setup_subparsers(self, parser):
        """process subparsers"""
        if 'subparsers' in self.options or self.subcommands:
            args, kwargs = self.options.get('subparsers', ((), {}))
            # kwargs['required'] = kwargs.pop(
            #     'required', not inspect.isfunction(self.definition.__call__))
            subparsers = parser.add_subparsers(*args, **kwargs)
            for name, command in self.subcommands.items():
                command.setup_parser(subparsers.add_parser, name)

    def __call__(self, args: List[str]=None):
        """Parse `args` and run the fitting command.

        :params:
           args:     List of command line arguments for argument parser
        """
        parser = self.setup_parser()
        namespace = parser.parse_args(args)

        try:
            func = namespace._func
        except AttributeError:
            return parser.print_usage()

        args = ()
        kwargs = {}
        for i, name in enumerate(inspect.signature(func).parameters):
            if i == 0 and name == 'self':
                try:
                    args = (self.options['bind'](parser, namespace),)
                except KeyError:
                    args = (namespace,)
            elif name in vars(namespace):
                kwargs[name] = getattr(namespace, name)
        return func(*args, **kwargs)
