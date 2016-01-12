# -*- coding: utf-8 -*-
"""
R_IRISSeismic - Python Wrappers for the IRISMustangMetrics R Package
===================================================
Capabilities include calculation of metrics.

:copyright:
    Mazama Science
:license:
    GNU Lesser General Public License, Version 3
    (http://www.gnu.org/copyleft/lesser.html)

"""
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
from future.builtins import *  # NOQA

from .metrics import *

if __name__ == '__main__':
    import doctest
    doctest.testmod(exclude_empty=True)

