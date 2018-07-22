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

# Always prefer setuptools over distutils
from setuptools import setup, find_packages
# To use a consistent encoding
import codecs
import re
import os.path

here = os.path.abspath(os.path.dirname(__file__))

version_file = os.path.join(here, 'lib', 'argparse_deco', 'version.py')
with codecs.open(version_file, 'rt') as fp:
    re_version = re.compile(
        r"""^__version__[ ]*=[ ]*["']{1,3}(.+)["']{1,3}$""")
    for line in fp:
        r = re_version.match(line)
        if r is not None:
            version = r.group(1)
            break
    else:
        raise RuntimeError("Cannot find version string in %s" % version_file)

# Get the long description from the README file
with codecs.open(os.path.join(here, 'README.rst'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='argparse-deco',

    # Versions should comply with PEP440.  For a discussion on single-sourcing
    # the version across setup.py and the project code, see
    # https://packaging.python.org/en/latest/single_source_version.html
    version=version,

    description='argparse-deco - Syntactic sugar for argparse',
    long_description=long_description,

    # The project's main homepage.
    url='https://github.com/zaehlwerk/argparse-deco',

    # Author details
    author='Gregor Giesen',
    author_email='giesen@zaehlwerk.net',

    # Choose your license
    license="GPLv3",

    # See https://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy',
        ],

    # What does your project relate to?
    keywords='cli',

    # You can just specify the packages manually here if your project is
    # simple. Or you can use find_packages().
    package_dir={'': 'lib'},
    packages=find_packages('lib', exclude=['tests']),

    # List run-time dependencies here.  These will be installed by pip when
    # your project is installed. For an analysis of "install_requires" vs pip's
    # requirements files see:
    # https://packaging.python.org/en/latest/requirements.html
    install_requires=[],

    # List additional groups of dependencies here (e.g. development
    # dependencies). You can install these using the following syntax,
    # for example:
    # $ pip install -e .[dev,test]
    extras_require={
        'test': ['pytest',
                 'pytest-cov',
                 'pytest-flakes',
                 'pytest-mock',
                 'pytest-pep8',
                 'pytest-runner'],
    },

    # If there are data files included in your packages that need to be
    # installed, specify them here.  If using Python 2.6 or less, then these
    # have to be included in MANIFEST.in as well.
    package_data={},

    tests_require=['pytest',
                   'pytest-cov',
                   'pytest-flakes',
                   'pytest-pep8',
                   'pytest-mock'],

    # To provide executable scripts, use entry points in preference to the
    # "scripts" keyword. Entry points provide cross-platform support and allow
    # pip to create the appropriate form of executable for the target platform.
    entry_points={},
)
