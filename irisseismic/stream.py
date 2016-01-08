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
from future.types import newint

import numpy as np

from obspy.core.utcdatetime import UTCDateTime


### ----------------------------------------------------------------------------


# Connect to R through the rpy2 module
import rpy2.robjects as robjects
r = robjects.r

# R options
r('options(digits.secs=6)')      # print out fractional seconds

# Load the IRISSeismic package
r('library(IRISSeismic)')


###   R functions called internally     ----------------------------------------


# NOTE:  These functions behave exactly the same as the R versions and require
# NOTE:  R-compatible objects as arguments.

# from base
_R_as_integer = r('base::as.integer')         # for conversion of python integers to R integer vectors
_R_as_POSIXct = r('base::as.POSIXct')         # for conversion of ISO datestrings to R POSIXct
_R_vector = r('base::vector')                 # for creation of a the list of Traces used in R_Trace
_R_list = r('base::list')                     # for creation of the headerList used in R_Trace

# from IRISSeismic
_R_initialize = r('IRISSeismic::initialize')  # initialization of various objects


###   Pythonic conversion functions     ----------------------------------------


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
    # NOTE:  ObsPy uses future.builtins which means that the integer values can be
    # NOTE:  of type 'future.types.newint.newint'. When passed to R, this is converted
    # NOTE:  to an integer value of 1 rather than the actual value. In the hack 
    # NOTE:  below, we obtain the string version of x and then use the R 
    # NOTE:  _R_as_integer() function to convert the string to the required integer value.
    
    # Convert vectors and single values into strings
    if isinstance(x,list):
        x = [str(a) for a in x]
    else:
        x = [str(x)]
    
    # Pass the array of strings to the R as.integer() function
    return _R_as_integer(x)


def R_float(x):
    """
    Creates an R float vector from a python ints, floats or a `numpy.ndarray`.
    :param x: python int, float or `numpy.ndarray`
    :return: R float vector
                
    .. rubric:: Example
    
    >>> R_float(int(3)) #doctest: +ELLIPSIS
    <FloatVector - Python:...>
    [3.000000]
    >>> R_float(3.5) #doctest: +ELLIPSIS
    <FloatVector - Python:...>
    [3.500000]
    >>> R_float([1.5,2.5,3.5]) #doctest: +ELLIPSIS
    <FloatVector - Python:...>
    [1.500000, 2.500000, 3.500000]
    >>> R_float(np.array([1.5,2.5,3.5])) #doctest: +ELLIPSIS
    <FloatVector - Python:...>
    [1.500000, 2.500000, 3.500000]
    """
    if isinstance(x,float) or isinstance(x, int) or isinstance(x, newint):
        x = [x]
    return robjects.vectors.FloatVector(x)


def R_POSIXct(x):
    """
    Creates an R POSIXct vector from a python '~obspy.core.utcdatetime.UTCDateTime'
    or list of `UTCDatetime`s.
    :param x: python `UTCDateTime` or list of `UTCDateTime`s
    :return: R POSIXct vector
           
    .. rubric:: Example
    
    >>> print(R_POSIXct(UTCDateTime("2010-11-12 13:14:15.1617")))
    [1] "2010-11-12 13:14:15.1617 GMT"
    <BLANKLINE>
    >>> print(R_POSIXct(None))
    [1] NA
    <BLANKLINE>
    >>> print(R_POSIXct(123)) #doctest: +ELLIPSIS
    Traceback (most recent call last):
    ...
    TypeError: Argument 'x' must be of type 'obspy.core.utcdatetime.UTCDateTime'.
    """
    if x is None:
        x = robjects.NA_Logical
        
    elif isinstance(x,UTCDateTime):
        # Convert vectors and single values into strings
        if isinstance(x,list):
            raise NotImplementedError("Argument 'x' does not yet support lists of 'UTCDateTime's.")
        else:
            x = x.isoformat()
    
    else:
        raise TypeError("Argument 'x' must be of type 'obspy.core.utcdatetime.UTCDateTime'.")
        
    # Pass the array of strings to the R as.integer() function
    return _R_as_POSIXct(x, format="%Y-%m-%dT%H:%M:%OS", tz="GMT")


def R_list(n):
    """
    Creates an empty R list of length `n`.
    :param n: length of list to be created
    :return: R list
           
    .. rubric:: Example
    
    >>> print(R_list(2))
    [[1]]
    NULL
    <BLANKLINE>
    [[2]]
    NULL
    <BLANKLINE>
    <BLANKLINE>
    """
    return _R_vector("list",n)


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
                           sampling_rate=R_float(stats.sampling_rate))
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
                           InstrumentSensitivity=R_float(instrument_sensitivity),
                           InputUnits=input_units,
                           data=R_float(trace.data))
    return R_Trace
    
    
###   Stream     ---------------------------------------------------------------


# TODO:  Support url, sensor, scale, scaleunits as arguments in R_Stream()

# TODO:  Should we automatically get channelInfo from R getChannels() as in
# TODO:  IRISSeismic::getDataselect.IrisClient()?

# TODO:  What about act_flags, io_flags, dq_flags and timing_qual?

def R_Stream(stream,
             requestedStarttime=None,
             requestedEndtime=None):
    """
    Create an IRISSeismic Stream from and ObsPy Stream object
    :param stream: ObsPy Stream object.
    :param requestedStarttime: ObsPy UTCDateTime object.
    :param requestedEndtime: ObsPy UTCDateTime object.
    :return: IRISSeismic Stream object
    """
    R_listOfTraces = R_list(len(stream.traces))
    for i in range(len(stream.traces)):
        R_listOfTraces[i] = R_Trace(stream.traces[i])
        
    R_Stream = r('new("Stream")')
    R_Stream = _R_initialize(R_Stream,
                             requestedStarttime=R_POSIXct(requestedStarttime),
                             requestedEndtime=R_POSIXct(requestedEndtime),
                             traces=R_listOfTraces)
    return(R_Stream)    


### ----------------------------------------------------------------------------


if __name__ == '__main__':
    import doctest
    doctest.testmod(exclude_empty=True)
