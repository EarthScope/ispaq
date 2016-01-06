#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Python module containing wrappers for the IRISSeismic R package.
:copyright:
    Mazama Science
:license:
    GNU Lesser General Public License, Version 3
    (http://www.gnu.org/copyleft/lesser.html)
"""
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
from future.builtins import *  # NOQA

#import numpy as np

# Connect to R through the rpy2 module
import rpy2.robjects as robjects
r = robjects.r

# R options
r('options(digits.secs=6)')      # print out decimal fractions

# Load the IRISSeismic package
r('library(IRISSeismic)')


###   Base R functions     -----------------------------------------------------

# For conversion of ISO datestrings to R POSIXct
R_asPOSIXct = r('as.POSIXct')

# For conversion of strings to R integers (see NOTE in R_createTraceHeader)
R_asinteger = r('as.integer')

    
###   TraceHeader     ----------------------------------------------------------

# From IRISSeismic/R/Utils.R:miniseed2Stream

#headerList <- list(network=segList[[i]]$network,
                   #station=segList[[i]]$station,
                   #location=segList[[i]]$location,
                   #channel=segList[[i]]$channel,
                   #quality=segList[[i]]$quality,
                   #starttime=as.POSIXct(segList[[i]]$starttime, origin=origin, tz="GMT"),
                   #npts=segList[[i]]$npts,
                   #sampling_rate=segList[[i]]$sampling_rate)

# Creation of a Trace Header list to pass as an argument to R_initialize()
R_createHeaderList = r('''
function(network,station,location,channel,quality,starttime,npts,sampling_rate) {
  list(network=network,
       station=station,
       location=location,
       channel=channel,
       quality=quality,
       starttime=starttime,
       npts=npts,
       sampling_rate=sampling_rate)
}''')

# Initialization of the IRISSeismic TraceHeader object
R_initialize = r('IRISSeismic::initialize')


# This is a python function that wraps R functions
def R_createTraceHeader(stats):
    """
    Create an IRISSeismic TraceHeader from and ObsPy stats object
    :param stats: ObsPy Stats object.
    :return: IRISSeismic TraceHeader object
    """
    # NOTE:  ObsPy uses future.builtins which means that the stats.npts values is
    # NOTE:  of type 'future.types.newint.newint'. When passed to R, this is converted
    # NOTE:  to an integer value of 1 rather than the actyual value. In the hack 
    # NOTE:  below we obtain the string version of stats.npts and then use the R 
    # NOTE:  as.integer() function to convert it to the required integer value.
    R_headerList = R_createHeaderList(stats.network,
                                      stats.station,
                                      stats.location,
                                      stats.channel,
                                      stats.mseed.dataquality,
                                      R_asPOSIXct(stats.starttime.isoformat(), format="%Y-%m-%dT%H:%M:%OS", tz="GMT"),
                                      R_asinteger(str(stats.npts)),
                                      stats.sampling_rate)
    R_TraceHeader = r('new("TraceHeader")')
    R_TraceHeader = R_initialize(R_TraceHeader, R_headerList)
    return R_TraceHeader


###   asdf ---------------------------------------------------------------------



if __name__ == '__main__':
    import doctest
    doctest.testmod(exclude_empty=True)
