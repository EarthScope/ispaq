#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Python module containing wrappers for the IRISMustangMetrics R package.
:copyright:
    Mazama Science
:license:
    GNU Lesser General Public License, Version 3
    (http://www.gnu.org/copyleft/lesser.html)
"""
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
from future.builtins import *  # NOQA


# Connect to R through the rpy2 module
import rpy2.robjects as robjects
r = robjects.r

# R options
r('options(digits.secs=6)')      # print out fractional seconds


###   Simple metrics functions that only take a Stream argument    -------------


# min, median, mean, max and rms of an R_Stream
R_basicStatsMetric = r('IRISMustangMetrics::basicStatsMetric')

# For conversion of ISO datestrings to R POSIXct
R_gapsMetric = r('IRISMustangMetrics::gapsMetric')

    

if __name__ == '__main__':
    import doctest
    doctest.testmod(exclude_empty=True)
