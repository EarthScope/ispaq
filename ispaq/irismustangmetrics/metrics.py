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


from obspy.core import UTCDateTime

from ispaq.irisseismic.webservices import R_getSNCL

# Connect to R through the rpy2 module
from rpy2.robjects import r, pandas2ri

# R options
r('options(digits.secs=6)')      # print out fractional seconds


###   R functions called internally     ----------------------------------------


# NOTE:  These functions behave exactly the same as the R versions and require
# NOTE:  R-compatible objects as arguments.

# IRISMustangMetrics helper functions
_R_metricList2DF = r('IRISMustangMetrics::metricList2DF')
_R_metricList2Xml = r('IRISMustangMetrics::metricList2Xml')


###   R functions still to be written     --------------------------------------


def listMetricFunctions(functionType="simple"):
    """
    Function to be added to the IRISMustangMetrics package.
    
    "simple" metrics are those that require only a single stream as input and
    return a metricList of SingleValueMetrics as output. They may may have
    additional arguments which can be used but the provided defaults are 
    typically adequate
    """
    functionList = ['basicStatsMetric',
                    'DCOffsetTimesMetric',
                    'gapsMetric',
                    'SNRMetric',
                    'spikesMetric',
                    'STALTAMetric',
                    'stateOfHealthMetric',
                    'upDownTimesMewtric']
    return(functionList)
 

###   Functions for SingleValueMetrics     -------------------------------------


def applyMetric(r_stream, metricName, **kwargs):
    # TODO:  use **kwargs
    function = 'IRISMustangMetrics::' + metricName + 'Metric'
    R_function = r(function)
    r_metricList = R_function(r_stream)
    r_dataframe = _R_metricList2DF(r_metricList)
    df = pandas2ri.ri2py(r_dataframe)
    # TODO:  How to automatically convert times
    starttime = []
    for i in range(len(df.starttime)):
        starttime.append(UTCDateTime(df.starttime[i]))
    df.starttime = starttime
    endtime = []
    for i in range(len(df.endtime)):
        endtime.append(UTCDateTime(df.endtime[i]))
    df.endtime = endtime
    return df


### ----------------------------------------------------------------------------


if __name__ == '__main__':
    import doctest
    doctest.testmod(exclude_empty=True)
