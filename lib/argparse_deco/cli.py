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
import collections
import functools
import inspect
import sys

from .compat import Base, OrderedClassMeta

__all__ = ('Base', 'parser', 'subparsers',
           'argument', 'group', 'mutually_exclusive',
           'main')

def CliDecorator(deco_or_name):
    if isinstance(deco_or_name, str):
        name = deco_or_name
    else:
        name = deco_or_name.__name__

    def cli_decorator(deco):
        def decorator_decorator(*args, **kwargs):
            def decorator(obj):
                try:
                    obj._cli_options
                except AttributeError:
                    obj._cli_options = dict()
                obj._cli_options[name] = deco(
                    obj._cli_options.get(name), *args, **kwargs)
                return obj
            return decorator
        return decorator_decorator

    if isinstance(deco_or_name, str):
        return cli_decorator
    return cli_decorator(deco_or_name)

@CliDecorator
def parser(option, *args, **kwargs):
    if option is None:
        return (args, kwargs)
    option[1].update(kwargs)
    return (args, option[1])

@CliDecorator('parser')
def alias(option, name):
    if option is None:
        option = ((), dict(aliases=[name]))
    elif 'aliases' not in option:
        option[1]['aliases'] = [name]
    else:
        option[1]['aliases'].append(name)
    return option

@CliDecorator
def argument(option, *args, **kwargs):
    if option is None:
        return [(args, kwargs)]
    option.append((args, kwargs))
    return option

@CliDecorator
def group(option, name, title=None, description=None):
    if option is None:
        option = collections.OrderedDict()
    option[name] = dict(title=title, description=description)
    return option

@CliDecorator
def mutually_exclusive(option, name, required=False):
    if option is None:
        option = {}
    option[name] = dict(required=required)
    return option

@CliDecorator
def subparsers(option, *args, **kwargs):
    return (args, kwargs)

def parse(obj, parser=None):
    cli_options = getattr(obj, '_cli_options', {})

    if parser is None:
        args, kwargs = cli_options.get('parser', ((), {}))
        desc = kwargs.pop('description', obj.__doc__)
        parser = argparse.ArgumentParser(*args, description=desc, **kwargs)

    # Setup argument groups
    groups = {}
    for name, kwargs in reversed(list(cli_options.get('group', {}).items())):
        groups[name] = parser.add_argument_group(**kwargs)
    for name, kwargs in reversed(list(
            cli_options.get('mutually_exclusive', {}).items())):
        if name in groups:
            raise argparse.ArgumentError(
                None, "Duplicate group: {}".format(name))
        groups[name] = parser.add_mutually_exclusive_group(**kwargs)

    # Setup arguments group-awarely
    for args, kwargs in reversed(cli_options.get('argument', [])):
        try:
            group = groups[kwargs.pop('group')]
        except KeyError:
            parser.add_argument(*args, **kwargs)
        else:
            group.add_argument(*args, **kwargs)

    # Setup default action
    if inspect.isfunction(obj):
        parser.set_defaults(__func=obj)
    elif inspect.isclass(obj):
        if inspect.isfunction(obj.__call__):
            parser.set_defaults(__func=obj.__call__)

        # Classes have subcommands
        args, kwargs = cli_options.get('subparsers', ((), {}))
        subparsers = parser.add_subparsers(*args, **kwargs)
        for name, subobj in (
                obj._ordered_namespace.items()
                if hasattr(obj, '_ordered_namespace')
                else inspect.getmembers(obj)):
            if not name.startswith('_'):
                args, kwargs = getattr(subobj, '_cli_options', {}).get(
                    'parser', ((), {}))
                parser_help = kwargs.pop('help', subobj.__doc__)
                parse(subobj, subparsers.add_parser(
                    getattr(subobj, '_alias', name),
                    *args, help=parser_help, **kwargs))
    else:
        raise Exception("NIY: "+repr(obj))
    return parser

def run(obj, *args, **kwargs):
    """Parse a Argument Parser definition and run it.

    :params:
      args:     Run function with these additional positional arguments.
      kwargs:   Run function with these additional keyword arguments.
                Those can be overwritten by the arguments from
                the parser. However, if '_override' is a dict
                in kwargs, those elements will overwrite even these.

    Example:
    g = run(obj)
    args, kwargs = next(g)
    # Do something with the arguments
    returncode = g.send((args, kwargs))

    """
    parser = parse(obj)
    override_kwargs = kwargs.pop('_override', {})
    kwargs.update(vars(parser.parse_args()))
    kwargs.update(override_kwargs)
    args, kwargs = yield (args, kwargs)
    try:
        func = kwargs.pop('__func')
    except KeyError:
        yield parser.print_usage()
    else:
        yield func(*args, **kwargs)

def main(obj_or_name):
    name = obj_or_name if isinstance(obj_or_name, str) else 'main'
    def decorator(obj):
        try:
            mod = sys.modules[obj.__module__]
        except KeyError:
            pass
        else:
            def main(hook, *args, **kwargs):
                g = run(obj, *args, **kwargs)
                return g.send(hook(*next(g)))
            main.hook = lambda args, kwargs: (args, kwargs)
            def hook(h):
                main.hook = h
                return h
            wrapper = functools.wraps(main)(
                lambda *args, **kwargs: main(main.hook, *args, **kwargs))
            wrapper.hook = hook
            setattr(mod, name, wrapper)
        return obj

    if isinstance(obj_or_name, str):
        return decorator
    return decorator(obj_or_name)
