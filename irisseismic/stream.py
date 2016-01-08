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

from obspy.core.utcdatetime import UTCDateTime


# Connect to R through the rpy2 module
import rpy2.robjects as robjects
r = robjects.r

# R options
r('options(digits.secs=6)')      # print out fractional seconds

# Load the IRISSeismic package
r('library(IRISSeismic)')


###   R functions called internally     ----------------------------------------


# NOTE:  These functions behave exactly the same as the R versions.
# NOTE:  For more pythonic versions, see below.

# from base
_R_as_integer = r('base::as.integer')         # for conversion of python integers to R integer vectors
_R_as_POSIXct = r('base::as.POSIXct')         # for conversion of ISO datestrings to R POSIXct
_R_vector = r('base::vector')                 # for creation of a the list of Traces used in R_Trace
_R_list = r('base::list')                     # for creation of the headerList used in R_Trace

# from IRISSeismic
_R_initialize = r('IRISSeismic::initialize')  # initialization of various objects


###   Pythonic versions of the base functions     ------------------------------


# NOTE:  These are pythonic data conversion functions that may behave slightly 
# NOTE:  differently from the `_R_~` functions defined above.

def R_integer(x):
    """
    Creates an R integer vector from a python integer or list of integers.
    :param x: python integer or list of integers
    :return: R integer vector
    
    .. note::
    
    The `x` argument may contain single values or lists of values with type
    'int', 'unicode' or 'future.types.newint.newint'.
            
    .. rubric:: Example
    
    >>> R_integer(3) #doctest: +ELLIPSIS
    <IntVector - Python:...>
    [       3]
    >>> R_integer(int(3)) #doctest: +ELLIPSIS
    <IntVector - Python:...>
    [       3]
    >>> R_integer('3') #doctest: +ELLIPSIS
    <IntVector - Python:...>
    [       3]
    >>> R_integer([1,2,3]) #doctest: +ELLIPSIS
    <IntVector - Python:...>
    [       1,        2,        3]
    """
    # NOTE:  ObsPy uses future.builtins which means that the integer values are often
    # NOTE:  of type 'future.types.newint.newint'. When passed to R, this is converted
    # NOTE:  to an integer value of 1 rather than the actual value. In the hack 
    # NOTE:  below, we obtain the string version of x and then use the R 
    # NOTE:  _R_as_integer() function to convert the string to the required integer value.
    
    # Convert vectors and single values into strings
    if type(x) == type([1,2,3]):
        x = [str(a) for a in x]
    else:
        x = [str(x)]
    
    # Pass the array of strings to the R as.integer() function
    return _R_as_integer(x)


def R_POSIXct(x):
    """
    Creates an R POSIXct vector from a python '~obspy.core.utcdatetime.UTCDateTime'
    or list of `UTCDatetime`s.
    :param x: python `UTCDateTime` or list of `UTCDateTime`s
    :return: R POSIXct vector
           
    .. rubric:: Example
    
    >>> t = UTCDateTime("2010-11-12 13:14:15.1617")
    >>> print(R_POSIXct(t))
    [1] "2010-11-12 13:14:15.1617 GMT"
    <BLANKLINE>
    """
    if type(x) is not UTCDateTime:
        raise TypeError("Argument 'x' must be of type 'obspy.core.utcdatetime.UTCDateTime'.")
    
    # Convert vectors and single values into strings
    if type(x) == type([1,2,3]):
        raise NotImplementedError("Argument 'x' does not yet support lists of 'UTCDateTime's.")
    else:
        x = x.isoformat()
    
    # Pass the array of strings to the R as.integer() function
    return _R_as_POSIXct(x, format="%Y-%m-%dT%H:%M:%OS", tz="GMT")


###   TraceHeader     ----------------------------------------------------------


def R_TraceHeader(stats):
    """
    Create an IRISSeismic TraceHeader from and ObsPy Stats object
    :param stats: ObsPy Stats object.
    :return: IRISSeismic TraceHeader object
    """
    R_headerList = _R_list(network=stats.network,
                           station=stats.station,
                           location=stats.location,
                           channel=stats.channel,
                           quality=stats.mseed.dataquality,
                           starttime=R_POSIXct(stats.starttime),
                           npts=R_integer(stats.npts),
                           sampling_rate=stats.sampling_rate)
    R_TraceHeader = r('new("TraceHeader")')
    R_TraceHeader = _R_initialize(R_TraceHeader, R_headerList)
    return R_TraceHeader


###   Trace     ----------------------------------------------------------------


def R_Trace(trace,
            sensor="",
            instrument_sensitivity=1.0,
            input_units=""):
    """
    Create an IRISSeismic Trace from and ObsPy Trace object
    :param trace: ObsPy Trace object.
    :param sensor: Seismometer instrument type.
    :param instrument_sensitivity: Channel sensitivity available from IRIS getChannel webservice.
    :param input_units: Units available from IRIS getChannel webservice.
    :return: IRISSeismic Trace object
    """
    R_Trace = r('new("Trace")')
    R_Trace = _R_initialize(R_Trace,
                           id=trace.id,
                           stats=R_TraceHeader(trace.stats),
                           Sensor=sensor,
                           InstrumentSensitivity=instrument_sensitivity,
                           InputUnits=input_units,
                           data=robjects.vectors.FloatVector(trace.data)) # TODO:  Should we have an R_data() function?
    return R_Trace
    
    
###   Stream     ---------------------------------------------------------------


# TODO:  Support sensor, scale, scaleunits as arguments in R_createStream()

# TODO:  Should we automatically get channelInfo from R getChannels() as in
# TODO:  IRISSeismic::getDataselect.IrisClient()?

def R_Stream(stream,
             requestedStarttime=None,  # TODO:  Shouldn't R_POSIXct handle missing values?
             requestedEndtime=None):
    """
    Create an IRISSeismic Stream from and ObsPy Stream object
    :param stream: ObsPy Stream object.
    :param requestedStarttime: ObsPy UTCDateTime object.
    :param requestedEndtime: ObsPy UTCDateTime object.
    :return: IRISSeismic Stream object
    """
    # Set defaults if no additional information is passed in    
    if requestedStarttime is None:
        requestedStarttime = robjects.NULL
    else:
        requestedStarttime = R_POSIXct(requestedStarttime)
        
    if requestedEndtime is None:
        requestedEndtime = robjects.NULL
    else:
        requestedEndtime = R_POSIXct(requestedEndtime)
     
    R_listOfTraces = _R_vector("list",len(stream.traces))
    for i in range(len(stream.traces)):
        R_listOfTraces[i] = R_Trace(stream.traces[i])
        
    R_Stream = r('new("Stream")')
    R_Stream = _R_initialize(R_Stream,
                             requestedStarttime=requestedStarttime,
                             requestedEndtime=requestedEndtime,
                             traces=R_listOfTraces)
    return(R_Stream)
     


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
