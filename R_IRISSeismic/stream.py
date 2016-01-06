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
r('options(digits.secs=6)')      # print out fractional seconds

# Load the IRISSeismic package
r('library(IRISSeismic)')


###   Base R functions     -----------------------------------------------------


# For conversion of strings to R integers (see NOTE in R_createTraceHeader)
R_as_integer = r('as.integer')

# For conversion of ISO datestrings to R POSIXct
R_as_POSIXct = r('as.POSIXct')

# For creation of a the list of Traces used in R_createTrace
R_vector = r('vector')
    
    
###   TraceHeader     ----------------------------------------------------------


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


def R_createTraceHeader(stats):
    """
    Create an IRISSeismic TraceHeader from and ObsPy Stats object
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
                                      R_as_POSIXct(stats.starttime.isoformat(), format="%Y-%m-%dT%H:%M:%OS", tz="GMT"),
                                      R_as_integer(str(stats.npts)),
                                      stats.sampling_rate)
    R_TraceHeader = r('new("TraceHeader")')
    R_TraceHeader = R_initialize(R_TraceHeader, R_headerList)
    return R_TraceHeader


###   Trace     ----------------------------------------------------------------


# TODO:  Support Sensor, etc. as arguments in R_createTrace

def R_createTrace(trace):
    """
    Create an IRISSeismic Trace from and ObsPy Trace object
    :param trace: ObsPy Trace object.
    :return: IRISSeismic Trace object
    """
    data = robjects.vectors.FloatVector(trace.data)
    R_TraceHeader = R_createTraceHeader(trace.stats)
    R_Trace = r('new("Trace")')
    R_Trace = R_initialize(R_Trace,
                           id="from_ObsPy",
                           stats=R_TraceHeader,
                           Sensor="Unknown Sensor",
                           InstrumentSensitivity=1.0,
                           InputUnits="",
                           data=data)
    return R_Trace
    
    
###   Stream     ---------------------------------------------------------------


# TODO:  Support Sensor, etc. as arguments in R_createStream

def R_createStream(stream):
    """
    Create an IRISSeismic Stream from and ObsPy Stream object
    :param stream: ObsPy Stream object.
    :return: IRISSeismic Stream object
    """
    R_listOfTraces = R_vector("list",len(stream.traces))
    for i in range(len(stream.traces)):
        R_listOfTraces[i] = R_createTrace(stream.traces[i])
    R_Stream = r('new("Stream")')
    R_Stream = R_initialize(R_Stream,
                            traces=R_listOfTraces)
     


#def R_createStream(stream,
                   #url=None,
                   #requestedStarttime=None,
                   #requestedEndtime=None,
                   #sensor=None,
                   #scale=None,
                   #scaleunits=None):
    #"""
    #Create an IRISSeismic Stream from and ObsPy Stream object
    #:param stream: ObsPy Stream object.
    #:return: IRISSeismic Stream object
    #"""
    ## Set defaults if no additional information is passed in
    #if url is None:
        #url = "unknown file"
        
    #if requestedStarttime is None:
        #requestedStarttime = robjects.NULL
    #else:
        #requestedStarttime = R_as_POSIXct(requestedStarttime.isoformat(), format="%Y-%m-%dT%H:%M:%OS", tz="GMT")
        
    #if requestedStarttime is None:
        #requestedStarttime = robjects.NULL
    #else:
        #requestedStarttime = R_as_POSIXct(requestedStarttime.isoformat(), format="%Y-%m-%dT%H:%M:%OS", tz="GMT")
        
    #if sensor is None:
        #sensor = ""
        
    #if scale is None:
        #scale = robjects.NA_Integer
        
    #if scaleUnits is None:
        #scaleUnits = ""
        
    
    
    
    
    
    
    
    
    
    
    #stream <- new("Stream", url=url, requestedStarttime=requestedStarttime, requestedEndtime=requestedEndtime,
                  #act_flags=act_flags, io_flags=io_flags, dq_flags=dq_flags, timing_qual=timing_qual,
                  #traces=traces)
    
    



if __name__ == '__main__':
    import doctest
    doctest.testmod(exclude_empty=True)
