# -*- coding: utf-8 -*-
"""
R_IRISSeismic - Python Wrappers for the IRISSeismic R Package
===================================================
Capabilities include creation of IRISSeismic Trace and Stream objects
from ObsPy Trace and Stream objects.

:copyright:
    Mazama Science
:license:
    GNU Lesser General Public License, Version 3
    (http://www.gnu.org/copyleft/lesser.html)

"""
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
from future.builtins import *  # NOQA

#from R_Stream import R_createTraceHeader
from .R_Stream import R_createTraceHeader

if __name__ == '__main__':
    import doctest
    doctest.testmod(exclude_empty=True)

#import numpy as np

## Connect to R through the rpy2 module
#import rpy2.robjects as robjects
#r = robjects.r

## Load the IRISSeismic package
#r('library(IRISSeismic)'


####   Base R functions     -----------------------------------------------------

## For conversion of ISO datestrings to R POSIXct
#R_asPOSIXct = r('as.POSIXct')

    
####   TraceHeader     ----------------------------------------------------------

## Creation of a Trace Header list to pass as an argument to R_initialize()
#R_createHeaderList = r('''
#function(network,station,location,channel,quality,starttime,endtime,npts,sampling_rate) {
  #list(network=network,
       #station=station,
       #location=location,
       #channel=channel,
       #quality=quality,
       #starttime=starttime,
       #endtime=endtime,
       #npts=npts,
       #sampling_rate=sampling_rate)
#}''')

## Initialization of the IRISSeismic TraceHeader object
#R_initialize = r('IRISSeismic::initialize')


## This is a python function that wraps R functions
#def R_createTraceHeader(stats):
    #"""
    #Create an IRISSeismic TraceHeader from and ObsPy stats object
    #:param stats: ObsPy Stats object.
    #:return: IRISSeismic TraceHeader object
    #"""
    #R_headerList = R_createHeaderList(stats.network,
                                      #stats.station,
                                      #stats.location,
                                      #stats.channel,
                                      #stats.mseed.dataquality,
                                      #R_asPOSIXct(stats.starttime.isoformat(), tz="GMT"),
                                      #R_asPOSIXct(stats.endtime.isoformat(), tz="GMT"),
                                      #stats.npts,
                                      #stats.sampling_rate)
    #R_TraceHeader = r('new("TraceHeader")')
    #R_TraceHeader = R_initialize(R_TraceHeader, R_headerList)
    #return R_TraceHeader
