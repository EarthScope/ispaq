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


### ----------------------------------------------------------------------------


# Connect to R through the rpy2 module
import rpy2.robjects as robjects
r = robjects.r

# R options
r('options(digits.secs=6)')      # print out fractional seconds


###   R functions called internally     ----------------------------------------


# NOTE:  These functions behave exactly the same as the R versions and require
# NOTE:  R-compatible objects as arguments.

# IRISMustangMetrics helper functions
_R_metricList2Xml = r('IRISMustangMetrics::metricList2Xml')

# IRISMustangMetrics metrics functions
_R_basicStatsMetric = r('IRISMustangMetrics::basicStatsMetric')
_R_gapsMetric = r('IRISMustangMetrics::gapsMetric')


###   Pythonic metrics functions     -------------------------------------------


def R_basicStatsMetric(R_Stream):
 R_MetricList = _R_basicStatsMetric(R_Stream)
 xml = _R_metricList2Xml(R_MetricList)
 return xml
 

# For conversion of ISO datestrings to R POSIXct
R_gapsMetric = r('IRISMustangMetrics::gapsMetric')


###   SingleValueMetric class     ----------------------------------------------


#print(_R_slotNames(bop))
 #[1] "snclq"                "starttime"            "endtime"             
 #[4] "metricName"           "valueName"            "value"               
 #[7] "valueString"          "quality_flag"         "quality_flagString"  
#[10] "attributeName"        "attributeValueString"


if __name__ == '__main__':
    import doctest
    doctest.testmod(exclude_empty=True)
