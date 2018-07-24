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

import pytest

from argparse_deco import version

def check(obj):
    """Checks whether obj is a string and nonempty"""
    return isinstance(obj, str) and obj

def test_version():
    assert check(version.__doc__)
    assert check(version.__author__)
    assert check(version.__copyright__)
    assert all(check(item) for item in version.__credits__)
    assert check(version.__license__)
    assert check(version.__version__)
    assert check(version.__maintainer__)
