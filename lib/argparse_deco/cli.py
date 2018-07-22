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

import argparse
import functools
import inspect
from typing import Any, ClassVar, Dict, List

from .compat import HAS_PY37, PEP560Meta
from .utils import ReadonlyAttribute


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


class CliMeta(type):

    def __new__(mcls, name, _, ns, **kwargs):
        for key, attr in ns.items():
            if not key.startswith('__') and inspect.isfunction(attr):
                ns[key] = mcls.wrap_function(attr)
        ns['__cli_options__'] = dict(parser=((), kwargs))
        return super().__new__(mcls, name, (), ns)

    @classmethod
    def wrap_function(mcls, func):
        return mcls(func.__name__, (Cli,), dict(
            __cli_options__=getattr(func, '__cli_options__', {}),
            __module__=func.__module__,
            __qualname__=func.__qualname__,
            __doc__=func.__doc__,
            __call__=func))

    @ReadonlyAttribute
    def subcommand(cls, command):
        if not issubclass(command, Cli):
            command = type(command.__name__, (Cli,), dict(vars(command)))
        setattr(cls, command.__name__, command)
        return command

    @ReadonlyAttribute
    def setup_parser(cls):
        cli_options = getattr(cls, '__cli_options__', {})

        # setup parser
        args, kwargs = cli_options.get('parser', ((), {}))
        if 'alias' in cli_options:
            kwargs['aliases'] = cli_options['alias']
        kwargs['description'] = kwargs.pop('description', cls.__doc__)
        parser = yield (args, kwargs)

        # setup arguments
        if inspect.isfunction(cls.__call__):
            signature = inspect.signature(cls.__call__)
            groups = dict()
            for name, kwargs in reversed(cli_options.get('group', ())):
                groups[name] = parser.add_argument_group(**kwargs)
            for name, kwargs in reversed(
                    cli_options.get('mutually_exclusive', ())):
                if name in groups:
                    raise argparse.ArgumentError(
                        None,
                        f"A regular group cannot be mutually exclusive: {name}")
                groups[name] = parser.add_mutually_exclusive_group(**kwargs)
            for name, parameter in signature.parameters.items():
                argument = parameter.annotation
                if isinstance(argument, Group):
                    try:
                        group = groups[argument.group]
                    except KeyError:
                        group = parser.add_argument_group()
                        groups[argument.group] = group
                    argument.apply(parameter, group.add_argument)
                elif isinstance(argument, Arg):
                    argument.apply(parameter, parser.add_argument)

            # setup default action
            parser.set_defaults(__func=cls.__call__)

        # process subcommands
        subbcommands = tuple(
            (name, command) for name, command in vars(cls).items()
            if inspect.isclass(command) and issubclass(command, Cli))
        if 'subparsers' in cli_options or subbcommands:
            args, kwargs = cli_options.get('subparsers', (((), {}),))[0]
            subparsers = parser.add_subparsers(*args, **kwargs)
            for name, command in subbcommands:
                gen = command.setup_parser()
                # obtain parser arguments from setup_parser
                args, kwargs = next(gen)
                if not args:
                    args = (name,)
                # continue setup_parser with parser instance
                gen.send(subparsers.add_parser(*args, **kwargs))

        yield

    @ReadonlyAttribute
    def get_parser(cls, factory=argparse.ArgumentParser):
        gen = cls.setup_parser()
        args, kwargs = next(gen)
        parser = factory(*args, **kwargs)
        gen.send(parser)
        return parser

    @ReadonlyAttribute
    def run(cls, *args, parser_kwargs={}, **kwargs):
        """Parse a Argument Parser definition and run it.

        :params:
          args:          Run function with these additional positional
                         arguments.
          parser_kwargs: Dictionary containing keyword arguments for
                         ArgumentParser.parse_args.
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
        parser = cls.get_parser()
        override_kwargs = kwargs.pop('_override', {})
        kwargs.update(vars(parser.parse_args(**parser_kwargs)))
        kwargs.update(override_kwargs)
        args, kwargs = yield (args, kwargs)
        try:
            func = kwargs.pop('__func')
        except KeyError:
            yield parser.print_usage()
        else:
            yield func(*args, **kwargs)

    def __call__(cls, *args, parser_kwargs={}, **kwargs):
        if cls is Cli:
            return cls.wrap_function(args[0])
        g = cls.run(*args, parser_kwargs=parser_kwargs, **kwargs)
        return g.send(next(g))


def cli_decorator(cli_deco=None, *, single=False):
    def wrapped_wrapper(deco):
        @functools.wraps(deco)
        def wrapper(*args, **kwargs):
            def decorator(command):
                if not isinstance(command, CliMeta):
                    command = CliMeta.wrap_function(command)
                try:
                    options = command.__cli_options__
                except AttributeError:
                    command.__cli_options__ = dict()
                if single:
                    options[deco.__name__] = deco(*args, **kwargs)
                else:
                    try:
                        option = options[deco.__name__]
                    except KeyError:
                        option = []
                        options[deco.__name__] = option
                    option.append(deco(*args, **kwargs))
                return command
            return decorator
        return staticmethod(wrapper)
    if cli_deco is None:
        return wrapped_wrapper
    return wrapped_wrapper(cli_deco)


class Cli(metaclass=CliMeta):

    __cli_options__: ClassVar[Dict[str, List[Any]]]

    @cli_decorator(single=True)
    def parser(*args, **kwargs):
        # signature = inspect.signature(argparse.ArgumentParser)
        # return signature.bind(*args, **kwargs)
        return args, kwargs

    @cli_decorator
    def group(name: str, title: str=None, description: str=None):
        return name, dict(title=title, description=description)

    @cli_decorator
    def mutually_exclusive(name: str, required: bool=False):
        return name, dict(required=required)

    @cli_decorator(single=True)
    def subparsers(*args, **kwargs):
        return args, kwargs

    @cli_decorator
    def alias(name: str):
        return name
