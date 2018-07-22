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
import inspect
from typing import Any, Dict, Union, Tuple

from .arguments import Arg


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
        if not inspect.isfunction(definition) and \
           not inspect.isclass(definition):
            raise TypeError(
                f"{definition!r} is neither a class nor a function")
        self.definition = definition
        self.options = dict()
        self.subcommands = dict(
            (name, Command(attr)) for name, attr in vars(definition).items()
            if not name.startswith('__') and (
                inspect.isfunction(attr) or inspect.isclass(attr)))

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
        self.setup_arguments(parser)
        self.setup_subparsers(parser)
        return parser

    def setup_arguments(self, parser):
        """process command's arguments"""
        function = self.definition if inspect.isfunction(self.definition) \
            else self.definition.__call__
        if inspect.isfunction(function):
            signature = inspect.signature(function)
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
            parser.set_defaults(__func=function)

    def setup_subparsers(self, parser):
        """process subparsers"""
        if 'subparsers' in self.options or self.subcommands:
            args, kwargs = self.options.get('subparsers', ((), {}))
            subparsers = parser.add_subparsers(*args, **kwargs)
            for name, command in self.subcommands.items():
                command.setup_parser(subparsers.add_parser, name)

    @property
    def parser(self):
        return self.setup_parser()

    def run(self, *args, cli_args: Tuple[str]=None, **kwargs):
        """Parse a Argument Parser definition and run it.

        :params:
          args:          Run function with these additional positional
                         arguments.
          cli_args:      Arguments to parse. Defaults to sys.args
          kwargs:        Run function with these additional keyword arguments.
                         Those can be overwritten by the arguments from
                         the parser. However, if '_override' is a dict
                         in kwargs, those elements will overwrite even these.

        Example:
        g = run(obj)
        args, kwargs = next(g)
        # Do something with the arguments
        returncode = g.send((args, kwargs))
        """
        parser = self.setup_parser()
        override_kwargs = kwargs.pop('_override', {})
        if cli_args:
            kwargs.update(vars(parser.parse_args(cli_args)))
        else:
            kwargs.update(vars(parser.parse_args()))
        kwargs.update(override_kwargs)
        args, kwargs = yield (args, kwargs)
        try:
            func = kwargs.pop('__func')
        except KeyError:
            yield parser.print_usage()
        else:
            yield func(*args, **kwargs)

    def __call__(self, *args, cli_args=None, **kwargs):
        gen = self.run(*args, cli_args=cli_args, **kwargs)
        return gen.send(next(gen))
