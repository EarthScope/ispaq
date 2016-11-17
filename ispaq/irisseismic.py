# -*- coding: utf-8 -*-
"""
Python module containing wrappers for the IRISSeismic R package.
:copyright:
    Mazama Science
:license:
    GNU Lesser General Public License, Version 3
    (http://www.gnu.org/copyleft/lesser.html)
"""

from __future__ import (absolute_import, division, print_function)
from future.types import newint
import pandas as pd
from obspy import UTCDateTime
from rpy2 import robjects
from rpy2 import rinterface
from rpy2.robjects import pandas2ri


#     R Initialization     -----------------------------------------------------

# Global R options are set here

# Do not show error messages generated inside of the R packages
robjects.r('options(show.error.messages=FALSE)')


#     R functions called internally     ----------------------------------------

# NOTE:  These functions behave exactly the same as the R versions and require
# NOTE:  R-compatible objects as arguments.

# from base
_R_assign = robjects.r('base::assign')                                # assign a name to an object
_R_get = robjects.r('base::get')                                      # get an object from a name
_R_as_integer = robjects.r('base::as.integer')                        # conversion of python integers to R integer vectors
_R_as_POSIXct = robjects.r('base::as.POSIXct')                        # conversion of ISO datestrings to R POSIXct
_R_vector = robjects.r('base::vector')                                # creation of a the list of Traces used in R_Trace
_R_list = robjects.r('base::list')                                    # creation of the headerList used in R_Trace

# from IRISSeismic
_R_initialize = robjects.r('IRISSeismic::initialize')                 # initialization of various objects

# All webservice functions from IRISSeismic
_R_getAvailability = robjects.r('IRISSeismic::getAvailability')       #
_R_getChannel = robjects.r('IRISSeismic::getChannel')                 #
_R_getDataselect = robjects.r('IRISSeismic::getDataselect')           #
_R_getDistaz = robjects.r('IRISSeismic::getDistaz')                   #
_R_getEvalresp = robjects.r('IRISSeismic::getEvalresp')               #
_R_getEvent = robjects.r('IRISSeismic::getEvent')                     #
_R_getNetwork = robjects.r('IRISSeismic::getNetwork')                 #
_R_getRotation = robjects.r('IRISSeismic::getRotation')               # TODO:  This returns 3 Streams
_R_getSNCL = robjects.r('IRISSeismic::getSNCL')                       #
_R_getStation = robjects.r('IRISSeismic::getStation')                 #
_R_getTraveltime = robjects.r('IRISSeismic::getTraveltime')           #
_R_getUnavailability = robjects.r('IRISSeismic::getUnavailability')   #

# IRISMustangMetrics helper functions
_R_metricList2DF = robjects.r('IRISMustangMetrics::metricList2DF')

#     Python --> R conversion functions    -------------------------------------


def R_integer(x):
    """
    Creates an R integer vector from a python integer or list of integers.
    :param x: Python integer or list of integers.
    :return: R integer vector.
    
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
    :param x: Python int, float or `numpy.ndarray`.
    :return: R float vector.
                
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


def R_character(x):
    """
    Creates an R character vector from a list of python strings.
    :param x: Python string.
    :return: R character vector.                
    """
    return robjects.vectors.StrVector(x)


def R_POSIXct(x):
    """
    Creates an R POSIXct vector from a python '~obspy.core.utcdatetime.UTCDateTime'
    or list of `UTCDatetime`s.
    :param x: Python `UTCDateTime` or list of `UTCDateTime`s.
    :return: R POSIXct vector.
           
    .. rubric:: Example
    
    >>> print(R_POSIXct(UTCDateTime("2010-11-12 13:14:15")))
    [1] "2010-11-12 13:14:15 GMT"
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
    :param n: Length of list to be created.
    :return: R list.
           
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


def R_TraceHeader(stats, latitude, longitude, elevation, depth, azimuth, dip):
    """
    Create an IRISSeismic TraceHeader from and ObsPy Stats object
    :param stats: ObsPy Stats object.
    :return: IRISSeismic TraceHeader object.
    """
    r_headerList = _R_list(network=stats.network,
                           station=stats.station,
                           location=stats.location,
                           channel=stats.channel,
                           quality=stats.mseed.dataquality,
                           starttime=R_POSIXct(stats.starttime),
                           endtime=R_POSIXct(stats.endtime),
                           npts=R_integer(stats.npts),
                           sampling_rate=R_float(stats.sampling_rate),
                           latitude=R_float(latitude),
                           longitude=R_float(longitude),
                           elevation=R_float(elevation),
                           depth=R_float(depth),
                           azimuth=R_float(azimuth),
                           dip=R_float(dip))
    r_traceHeader = robjects.r('new("TraceHeader")')
    r_traceHeader = _R_initialize(r_traceHeader, r_headerList)
    return r_traceHeader


def R_Trace(trace,
            sensor="",
            scale=1.0,
            scalefreq=1.0,
            scaleunits="",
            latitude=None,
            longitude=None,
            elevation=None,
            depth=None,
            azimuth=None,
            dip=None):
    """
    Create an IRISSeismic Trace from and ObsPy Trace object
    :param trace: ObsPy Trace object.
    :param sensor: Seismometer instrument type.
    :param instrument_sensitivity: Channel sensitivity available from IRIS getChannel webservice.
    :param input_units: Units available from IRIS getChannel webservice.
    :return: IRISSeismic Trace object.
    """
    r_trace = robjects.r('new("Trace")')
    r_trace = _R_initialize(r_trace,
                           id=trace.id,
                           stats=R_TraceHeader(trace.stats, latitude, longitude, elevation, depth, azimuth, dip),
                           Sensor=sensor,
                           InstrumentSensitivity=scale, 
                           SensitivityFrequency=scalefreq,  
                           InputUnits=scaleunits,
                           data=R_float(trace.data))
    return r_trace
    
    
def R_Stream(stream,
             requestedStarttime=None,
             requestedEndtime=None,
             act_flags=[0,0,0,0,0,0,0,0],
             io_flags=[0,0,0,0,0,0,0,0],
             dq_flags=[0,0,0,0,0,0,0,0],
             sensor="",
             scale=1.0,
             scalefreq=1.0,
             scaleunits="",
             latitude=None,
             longitude=None,
             elevation=None,
             depth=None,
             azimuth=None,
             dip=None):
    """
    Create an IRISSeismic Stream from and ObsPy Stream object
    :param stream: ObsPy Stream object.
    :param requestedStarttime: ObsPy UTCDateTime object.
    :param requestedEndtime: ObsPy UTCDateTime object.
    :return: IRISSeismic Stream object.
    """
    
    # TODO:  Support url, sensor, scale, scaleunits as arguments in R_Stream()
    
    # TODO:  Should we automatically get channelInfo from R getChannels() as in
    # TODO:  IRISSeismic::getDataselect.IrisClient()?
    
    # Handle missing times
    if requestedStarttime is None:
        requestedStarttime = stream.traces[0].stats.starttime
    if requestedEndtime is None:
        requestedEndtime = stream.traces[-1].stats.endtime
        
    # Create R list of Trace objects
    r_listOfTraces = R_list(len(stream.traces))
    for i in range(len(stream.traces)):
        r_listOfTraces[i] = R_Trace(stream.traces[i], sensor, scale, scalefreq, scaleunits, latitude, longitude, elevation, depth, azimuth, dip)
        
    # Create R Stream object
    r_stream = robjects.r('new("Stream")')
    r_stream = _R_initialize(r_stream,
                             requestedStarttime=R_POSIXct(requestedStarttime),
                             requestedEndtime=R_POSIXct(requestedEndtime),
                             act_flags=R_integer(act_flags),
                             io_flags=R_integer(io_flags),
                             dq_flags=R_integer(dq_flags),
                             traces=r_listOfTraces)
    return(r_stream) 


# ------------------------------------------------------------------------------



#     Helper functions     ----------------------------------------------------


# TODO:  Probably could subsume more argument conversion in this single function.
def _R_args(*args):
    """
    Convert any arguments that are `None` or `newint` to R's
    `missing` and `integer`. Arguments of type `character` or `float`
    are retured unmodified.
    """
    r_args = []
    for arg in args:
        if arg is None:
            r_args.append(rinterface.MissingArg)
        elif isinstance(arg,newint):
            ###r_args.append(R_integer(arg))
            r_args.append(arg)
        else:
            r_args.append(arg)
            
    return tuple(r_args)

    
def _R_stationExtraArgs(includerestricted, latitude, longitude, minradius, maxradius):
    """
    Validate location-radius arguments.
    
    Make sure that if any of these are defined then lat, lon
    and at least one of the radii are defined. Then, convert
    any None values to `rpy2.rinterface.MissingArg`.
    
    Several webservices support location-radius arguments.

    """
    if includerestricted is None: 
        includerestricted = rinterface.MissingArg 
        
    if any([latitude,longitude,minradius,maxradius]):
        if all([latitude,longitude]) and any([minradius,maxradius]):
            # TODO:  Could add domain validation of values at this point
            if minradius is None:
                minradius = rinterface.MissingArg
            elif maxradius is None:
                maxradius = rinterface.MissingArg
            return (includerestricted, latitude, longitude, minradius, maxradius)
        else:
            raise ValueError('One of "longitude", "latitude" or "radius" is missing')
    else:
        return (includerestricted, rinterface.MissingArg, rinterface.MissingArg, rinterface.MissingArg, rinterface.MissingArg)


#     Python wrappers for R get~ webservice functions     ---------------------


def getAvailability(client_url="http://service.iris.edu",
                    network=None, station=None, location=None, channel=None,
                    starttime=None, endtime=None, includerestricted=None,
                    latitude=None, longitude=None,
                    minradius=None, maxradius=None):
    """
    Returns a pandas dataframe with channel metadata.
    :param network: sncl network (string)
    :param station: sncl station (string)
    :param location: sncl location (string)
    :param channel: sncl channel (string)
    :param starttime: ObsPy UTCDateTime object.
    :param endtime: ObsPy UTCDateTime object.
    :param includerestricted: TODO
    :param latitude: Optional latitude used when specifying a location and radius.
    :param longitude: Optional longitude used when specifying a location and radius.
    :param minradius: Optional minimum radius used when specifying a location and radius.
    :param maxradius: Optional maximum radius used when specifying a location and radius.
    :return: pandas dataframe of channel metadata.

    .. rubric:: Example

    >>> df = getAvailability("http://service.iris.edu", 'US', 'OXF', '', '', UTCDateTime("2012-06-21"), UTCDateTime("2012-06-28"))
    >>> df.shape
    (15, 18)
    >>> df.scale  #doctest: +ELLIPSIS
    1     629145000
    2     629145000
    ...
    """
    cmd = 'new("IrisClient", site="' + client_url + '")'
    r_client = robjects.r(cmd)
    starttime = R_POSIXct(starttime)
    endtime = R_POSIXct(endtime)
    (includerestricted, latitude, longitude, minradius, maxradius) = _R_stationExtraArgs(includerestricted, latitude, longitude, minradius, maxradius)
    
    # Call the function and return a pandas dataframe with the results
    r_df = _R_getAvailability(r_client, network, station, location, channel, starttime, endtime, includerestricted,
                              latitude, longitude, minradius, maxradius)
    df = pandas2ri.ri2py(r_df)
    
    # Convert columns from R POSIXct to python UTCDateTime
    df.starttime = df.starttime.apply(UTCDateTime)
    df.endtime = df.endtime.apply(UTCDateTime)
    
    return df

def getChannel(client_url="http://service.iris.edu",
               network=None, station=None, location=None, channel=None,
               starttime=None, endtime=None, includerestricted=False,
               latitude=None, longitude=None,
               minradius=None, maxradius=None):
    """
    Returns a pandas dataframe with channel metadata.
    :param network: sncl network (string)
    :param station: sncl station (string)
    :param location: sncl location (string)
    :param channel: sncl channel (string)
    :param starttime: ObsPy UTCDateTime object.
    :param endtime: ObsPy UTCDateTime object.
    :param includerestricted: TODO
    :param latitude: Optional latitude used when specifying a location and radius.
    :param longitude: Optional longitude used when specifying a location and radius.
    :param minradius: Optional minimum radius used when specifying a location and radius.
    :param maxradius: Optional maximum radius used when specifying a location and radius.
    :return: pandas dataframe of channel metadata.

    .. rubric:: Example

    >>> df = getChannel("http://service.iris.edu", 'US', 'OXF', '', '', UTCDateTime("2012-06-21"), UTCDateTime("2012-06-28"))
    >>> df.shape
    (18, 18)
    >>> df.scale  #doctest: +ELLIPSIS
    1     629145000
    2     629145000
    ...
    """
    cmd = 'new("IrisClient", site="' + client_url + '")'
    r_client = robjects.r(cmd)

    # Convert python arguments to R equivalents
    starttime = R_POSIXct(starttime)
    endtime = R_POSIXct(endtime)
    (includerestricted, latitude,longitude,minradius,maxradius) = _R_stationExtraArgs(includerestricted, latitude, longitude, minradius, maxradius)
    
    # Call the function and return a pandas dataframe with the results
    r_df = _R_getChannel(r_client, network, station, location, channel, starttime, endtime, includerestricted, latitude, longitude, minradius, maxradius)
    df = pandas2ri.ri2py(r_df)
    
    # Convert columns from R POSIXct to python UTCDateTime
    df.starttime = df.starttime.apply(UTCDateTime)
    df.endtime = df.endtime.apply(UTCDateTime)
    
    return df


def R_getDataselect(client_url="http://service.iris.edu",
                    network=None, station=None, location=None, channel=None,
                    starttime=None, endtime=None, quality="B",
                    inclusiveEnd=True, ignoreEpoch=False):
    """
    Obtain an R Stream using the IRISSeismic::getDataselect function.
    :param client_url: FDSN web services site URL
    :param network: sncl network (string)
    :param station: sncl station (string)
    :param location: sncl location (string)
    :param channel: sncl channel (string)
    :param starttime: ObsPy UTCDateTime object.
    :param endtime: ObsPy UTCDateTime object.
    :return: R Stream object
    :return: pandas dataframe of channel metadata.
    """
    cmd = 'new("IrisClient", site="' + client_url + '")'
    r_client = robjects.r(cmd)
    
    # Convert python arguments to R equivalents
    starttime = R_POSIXct(starttime)
    endtime = R_POSIXct(endtime)
    (quality, inclusiveEnd, ignoreEpoch)=_R_args(quality, inclusiveEnd, ignoreEpoch)
       
    # Call the function and return an R Stream
    r_stream = _R_getDataselect(r_client, network, station, location, channel, starttime, endtime, quality, inclusiveEnd, ignoreEpoch)
    
    return r_stream


def getDistaz(latitude, longitude, staLatitude, staLongitude):
    """
    Returns a pandas dataframe with great circle distance data from the IRIS DMC distaz webservice.
    :param latitude: Latitude of seismic event.
    :param longitude: Longitude of seismic event.
    :param staLatitude: Latitude of seismic station.
    :param staLongitude: Longitude of seismic station.
    :return: pandas dataframe with a single row containing ``azimuth, backAzimuth, distance``.

    .. rubric:: Example

    >>> df = getDistaz(-146, 45, 10, 10)
    >>> df
         azimuth  backAzimuth  distance
    1  241.57595     47.88017  39.97257
    """
    r_client = robjects.r('new("IrisClient")')
    
    # Call the function and return a pandas dataframe with the results
    r_df = _R_getDistaz(r_client, latitude, longitude, staLatitude, staLongitude)
    df = pandas2ri.ri2py(r_df)
    return df
    

def getEvalresp(network=None, station=None, location=None, channel=None,
                time=None, minfreq=None, maxfreq=None,
                nfreq=None, units=None, output="fap"):
    """
    Returns a pandas dataframe with cinstrument response data from the IRIS DMC evalresp webservice.
    :param network: sncl network (string)
    :param station: sncl station (string)
    :param location: sncl location (string)
    :param channel: sncl channel (string)
    :param time: ObsPy UTCDateTime object specifying the time at which the response is evaluated.
    :param minfreq: Optional minimum frequency at which the response is evaluated.
    :param maxfreq: Optional maximum frequency at which the response is evaluated.
    :param nfreq: Optional number of frequencies at which response will be evaluated.
    :param units: Optional code specifying unit conversion.
    :param output: Output type ['fap'|'cs'].
    :return: pandas dataframe of response metadata.

    .. rubric:: Example

    >>> df = getDistaz(-146, 45, 10, 10)
    >>> df
         azimuth  backAzimuth  distance
    1  241.57595     47.88017  39.97257
    """
    r_client = robjects.r('new("IrisClient")')
    
    # Convert python arguments to R equivalents
    time = R_POSIXct(time)
    (minfreq, maxfreq, nfreq, units, output) = _R_args(minfreq, maxfreq, nfreq, units, output)
    
    # Call the function and return a pandas dataframe with the results
    r_df = _R_getEvalresp(r_client, network, station, location, channel, time, minfreq, maxfreq, nfreq, units, output)
    df = pandas2ri.ri2py(r_df)
    return df
    
    
def getEvent(client_url="http://service.iris.edu", starttime=None, endtime=None,
             minmag=None, maxmag=None, magtype=None,
             mindepth=None, maxdepth=None):
    """
    Returns a pandas dataframe with channel metadata.
    :param starttime: ObsPy UTCDateTime object.
    :param endtime: ObsPy UTCDateTime object.
    :param minmag: Optional minimum magnitude.
    :param maxmag: Optional maximum magnitude.
    :param magtype:Optional magnitude type
    :param mindepth: Optional minimum depth (km).
    :param maxdepth: ptional maximum depth (km).
    :return: pandas dataframe of event metadata.
    
    .. rubric:: Example
    
    >>> df = getEvent("http://service.iris.edu", UTCDateTime("2012-06-21"), UTCDateTime("2012-06-28"), minmag=6)
    >>> df.shape
    (2, 13)
    >>> df.eventLocationName  #doctest: +ELLIPSIS
    2    NORTHERN SUMATERA, INDONESIA
    1    NEAR EAST COAST OF KAMCHATKA
    Name: eventLocationName, dtype: object
    """
    cmd = 'new("IrisClient", site="' + client_url + '")'
    r_client = robjects.r(cmd)
    
    # Convert python arguments to R equivalents
    starttime = R_POSIXct(starttime)
    endtime = R_POSIXct(endtime)
    (minmag, maxmag, magtype, mindepth, maxdepth) = _R_args(minmag, maxmag, magtype, mindepth, maxdepth)
    
    # Call the function and return a pandas dataframe with the results
    r_df = _R_getEvent(r_client, starttime, endtime, minmag, maxmag, magtype, mindepth, maxdepth)
    df = pandas2ri.ri2py(r_df)
    
    # Convert columns from R POSIXct to python UTCDateTime
    df.time = df.time.apply(UTCDateTime)
     
    return df
        
    
def getNetwork(client_url="http://service.iris.edu",
               network=None, station=None, location=None, channel=None,
               starttime=None, endtime=None, includerestricted=None,
               latitude=None, longitude=None,
               minradius=None, maxradius=None):
    """
    Returns a pandas dataframe with network metadata.
    :param network: sncl network (string)
    :param station: sncl station (string)
    :param location: sncl location (string)
    :param channel: sncl channel (string)
    :param starttime: ObsPy UTCDateTime object.
    :param endtime: ObsPy UTCDateTime object.
    :param includerestricted: TOOD
    :param latitude: Optional latitude used when specifying a location and radius.
    :param longitude: Optional longitude used when specifying a location and radius.
    :param minradius: Optional minimum radius used when specifying a location and radius.
    :param maxradius: Optional maximum radius used when specifying a location and radius.
    :return: pandas dataframe of network metadata.
    """
    cmd = 'new("IrisClient", site="' + client_url + '")'
    r_client = robjects.r(cmd)

    # Convert python arguments to R equivalents
    starttime = R_POSIXct(starttime)
    endtime = R_POSIXct(endtime)
    (includerestricted, latitude,longitude,minradius,maxradius) = _R_stationExtraArgs(includerestricted, latitude, longitude, minradius, maxradius)
    
    # Call the function and return a pandas dataframe with the results
    r_df = _R_getNetwork(r_client, network, station, location, channel, starttime, endtime, includerestricted, latitude, longitude, minradius, maxradius)
    df = pandas2ri.ri2py(r_df)
    
    # Convert columns from R POSIXct to python UTCDateTime
    df.starttime = df.starttime.apply(UTCDateTime)
    df.endtime = df.endtime.apply(UTCDateTime)
    
    return df
    
    
def R_getSNCL(client_url="http://service.iris.edu", sncl=None, starttime=None, endtime=None,
              quality="B"):
    """
    Obtain an R Stream using the IRISSeismic::getSNCL function.
    :param client_url: FDSN web services site URL
    :param sncl: SNCL (e.g. "US.OXF..BHZ")
    :param starttime: ObsPy UTCDateTime object.
    :param endtime: ObsPy UTCDateTime object.
    :return: R Stream object
    """
    cmd = 'new("IrisClient", site="' + client_url + '")'
    r_client = robjects.r(cmd)

    # Convert python arguments to R equivalents
    starttime = R_POSIXct(starttime)
    endtime = R_POSIXct(endtime)
        
    # Call the function and return a pandas dataframe with the results
    r_stream = _R_getSNCL(r_client, sncl, starttime, endtime, quality)
    return r_stream
    
    
def getStation(client_url="http://service.iris.edu",
               network=None, station=None, location=None, channel=None,
               starttime=None, endtime=None, includerestricted=None,
               latitude=None, longitude=None,
               minradius=None, maxradius=None):
    """
    Returns a pandas dataframe with station metadata.
    :param network: sncl network (string)
    :param station: sncl station (string)
    :param location: sncl location (string)
    :param channel: sncl channel (string)
    :param starttime: ObsPy UTCDateTime object.
    :param endtime: ObsPy UTCDateTime object.
    :param includerestricted: TODO
    :param latitude: Optional latitude used when specifying a location and radius.
    :param longitude: Optional longitude used when specifying a location and radius.
    :param minradius: Optional minimum radius used when specifying a location and radius.
    :param maxradius: Optional maximum radius used when specifying a location and radius.
    :return: pandas dataframe of channel metadata.
    """
    cmd = 'new("IrisClient", site="' + client_url + '")'
    r_client = robjects.r(cmd)

    # Convert python arguments to R equivalents
    starttime = R_POSIXct(starttime)
    endtime = R_POSIXct(endtime)
    (includerestricted, latitude,longitude,minradius,maxradius) = _R_stationExtraArgs(includerestricted, latitude, longitude, minradius, maxradius)
    
    # Call the function and return a pandas dataframe with the results
    r_df = _R_getStation(r_client, network, station, location, channel, starttime, endtime, includerestricted, latitude, longitude, minradius, maxradius)
    df = pandas2ri.ri2py(r_df)
    
    # Convert columns from R POSIXct to python UTCDateTime
    df.starttime = df.starttime.apply(UTCDateTime)
    df.endtime = df.endtime.apply(UTCDateTime)
    
    return df


def getTraveltime(latitude, longitude, depth, staLatitude, staLongitude):
    """
    Returns a pandas dataframe with seismic traveltime data from the IRIS DMC traveltime web service.
    :param latitude: Latitude of seismic event.
    :param longitude: Longitude of seismic event.
    :param staLatitude: Latitude of seismic station.
    :param staLongitude: Longitude of seismic station.
    :return: pandas dataframe with columns: ``distance, depth, phaseName, travelTime, rayParam, takeoff, incident, puristDistance, puristName``.
    """
    r_client = robjects.r('new("IrisClient")')
    
    # Call the function and return a pandas dataframe with the results
    r_df = _R_getTraveltime(r_client, latitude, longitude, depth, staLatitude, staLongitude)
    df = pandas2ri.ri2py(r_df)
    return df
    
    
def getUnavailability(client_url="http://service.iris.edu",
               network=None, station=None, location=None, channel=None,
               starttime=None, endtime=None, includerestricted=None,
               latitude=None, longitude=None,
               minradius=None, maxradius=None):
    """
    Returns a pandas dataframe with channel metadata for non-available channels.
    :param network: sncl network (string)
    :param station: sncl station (string)
    :param location: sncl location (string)
    :param channel: sncl channel (string)
    :param starttime: ObsPy UTCDateTime object.
    :param endtime: ObsPy UTCDateTime object.
    :param includerestricted: TODO
    :param latitude: Optional latitude used when specifying a location and radius.
    :param longitude: Optional longitude used when specifying a location and radius.
    :param minradius: Optional minimum radius used when specifying a location and radius.
    :param maxradius: Optional maximum radius used when specifying a location and radius.
    :return: pandas dataframe of channel metadata.
    """
    cmd = 'new("IrisClient", site="' + client_url + '")'
    r_client = robjects.r(cmd)
    
    # Convert python arguments to R equivalents
    starttime = R_POSIXct(starttime)
    endtime = R_POSIXct(endtime)
    (includerestricted, latitude,longitude,minradius,maxradius) = _R_stationExtraArgs(includerestricted, latitude, longitude, minradius, maxradius)    

    # Call the function and return a pandas dataframe with the results
    r_df = _R_getUnavailability(r_client, network, station, location, channel,
                                starttime, endtime, includerestricted,
                                latitude, longitude, minradius, maxradius)
    df = pandas2ri.ri2py(r_df)
    
    # Convert columns from R POSIXct to python UTCDateTime
    df.starttime = df.starttime.apply(UTCDateTime)
    df.endtime = df.endtime.apply(UTCDateTime)
    
    return df


#     Python wrappers for R non-webservice functions     -----------------------

# surfaceDistance is needed in crossCorrelation_metrics.py
def surfaceDistance(lat1, lon1, lat2, lon2):
    R_function = robjects.r('IRISSeismic::surfaceDistance')
    r_result = R_function(R_float(lat1), R_float(lon1), R_float(lat2), R_float(lon2))
    result = pandas2ri.ri2py(r_result)
    
    return(result)

# multiplyBy is needed in crossCorrelation_metrics.py
def multiplyBy(x, y):
    R_function = robjects.r('IRISSeismic::multiplyBy')
    r_stream = R_function(x, R_float(y))
    
    return(r_stream)

# mergeTraces is needed in pressureCorrelation_metrics.py
def mergeTraces(r_stream):
    R_function = robjects.r('IRISSeismic::mergeTraces')
    r_stream = R_function(r_stream)
    
    return(r_stream)

# butter is needed in crossCorrelation_metrics.py
def butter(x, y):
    R_function = robjects.r('signal::butter')
    r_filter = R_function(R_float(x), R_float(y))
    
    return(r_filter)

# trim_taper_filter is needed in orientationCheck_metrics.py
def trim_taper_filter(stN, stE, stZ, max_length, taper, filterArgs):
    """
    This function captures some of the functionality from generateMetrics_orientationCheck.R
    that involves direct manipulation of individual slots in Stream objects.
    This requires some R knowledge and rpy2 trickery that doesn't belong in the 
    business logic python code.
    """
    
    # Assign names in R
    _R_assign('stN',stN)
    _R_assign('stE',stE)
    _R_assign('stZ',stZ)
    
    # Adjust length
    robjects.r('stN@traces[[1]]@data <- stN@traces[[1]]@data[1:%d]' % (max_length))
    robjects.r('stE@traces[[1]]@data <- stE@traces[[1]]@data[1:%d]' % (max_length))
    robjects.r('stZ@traces[[1]]@data <- stZ@traces[[1]]@data[1:%d]' % (max_length))
    robjects.r('stN@traces[[1]]@stats@npts = as.integer(%d)' % (max_length))
    robjects.r('stE@traces[[1]]@stats@npts = as.integer(%d)' % (max_length))
    robjects.r('stZ@traces[[1]]@stats@npts = as.integer(%d)' % (max_length))
    
    # taper and filter traces
    robjects.r('N <- IRISSeismic::DDT(stN@traces[[1]],TRUE,TRUE,%s)' % (taper))
    robjects.r('E <- IRISSeismic::DDT(stE@traces[[1]],TRUE,TRUE,%s)' % (taper))
    robjects.r('Z <- IRISSeismic::DDT(stZ@traces[[1]],TRUE,TRUE,%s)' % (taper))

    robjects.r('N <- IRISSeismic::butterworth(N,%s,%s,%s)' % (filterArgs[0],filterArgs[1],filterArgs[2]))
    robjects.r('E <- IRISSeismic::butterworth(E,%s,%s,%s)' % (filterArgs[0],filterArgs[1],filterArgs[2]))
    robjects.r('Z <- IRISSeismic::butterworth(Z,%s,%s,%s)' % (filterArgs[0],filterArgs[1],filterArgs[2]))

    # Now put modified traces back into the Streams so that they can be rotated
    robjects.r('stN@traces[[1]] <- N')
    robjects.r('stE@traces[[1]] <- E')
    robjects.r('stZ@traces[[1]] <- Z')

    # Hilbert tansform of Z channel
    HZ = robjects.r('IRISSeismic::hilbert(Z)')

    # Get R objects back into python memory space
    stN = _R_get('stN')
    stE = _R_get('stE')
    stZ = _R_get('stZ')
    
    return(stN, stE, stZ, HZ)


# rotate2D is needed in orientationCheck_metrics.py
def rotate2D(st1, st2, angle):
    R_function = robjects.r('IRISSeismic::rotate2D')
    r_list = R_function(st1, st2, angle)
    
    returnList = []
    returnList.append(r_list[0])
    returnList.append(r_list[1])
    
    return(returnList)

# singleValueMetric is needed in orientationCheck_metrics.py
def singleValueMetric(snclq, starttime, endtime, metricName, value, attributeName, attributeValues):
    # Convert python arguments to R equivalents
    starttime = R_POSIXct(starttime)
    endtime = R_POSIXct(endtime)
    quality_flag = -9
    attributeName = R_character(attributeName)
    attributeValueString = R_character(attributeValues)
    
    R_function = robjects.r('methods::new')
    r_metric = R_function("SingleValueMetric", snclq, starttime, endtime,
                          metricName, value, quality_flag,
                          attributeName,
                          attributeValueString)
    

    r_metricList = _R_list(r_metric)
    r_dataframe = _R_metricList2DF(r_metricList)
    df = pandas2ri.ri2py(r_dataframe)

    return(df)

# generalValueMetric

def generalValueMetric(snclq, starttime, endtime, metricName, elementNames, elementValues, valueStrings=None):
    starttime = R_POSIXct(starttime)
    endtime = R_POSIXct(endtime)
    quality_flag = -9
    elementNames = R_character(elementNames)
    elementValues = R_character(elementValues)
    R_function = robjects.r('methods::new')
    if valueStrings is not None:
        valueStrings = R_character(valueStrings)
        r_metric = R_function("GeneralValueMetric", snclq, starttime, endtime, metricName, elementNames, elementValues, valueStrings)
    else:
        r_metric = R_function("GeneralValueMetric", snclq, starttime, endtime, metricName, elementNames, elementValues)
    r_metricList = _R_list(r_metric)
    r_dataframe = _R_metricList2DF(r_metricList)
    df = pandas2ri.ri2py(r_dataframe)

    return(df) 

# ------------------------------------------------------------------------------



if __name__ == '__main__':
    import doctest
    doctest.testmod(exclude_empty=True)
