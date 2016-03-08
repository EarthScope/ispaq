# -*- coding: utf-8 -*-
"""
Python module containing wrappers for the IRISSeismic R package.
:copyright:
    Mazama Science
:license:
    GNU Lesser General Public License, Version 3
    (http://www.gnu.org/copyleft/lesser.html)
    
ObsPy provides access to various IRIS webservices but these are returned
as python objects. Here we utilize the IRISSeismic R package to obtain
R objects which an be passed directly to the R metric functions.
"""
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
from future.builtins import *  # NOQA
from future.types import newint

import numpy as np

from obspy.core.utcdatetime import UTCDateTime

from ispaq.irisseismic.stream import *


### ----------------------------------------------------------------------------


# Connect to R through the rpy2 module
from rpy2.robjects import r, pandas2ri
import rpy2.rinterface as ri

# R options
r('options(digits.secs=6)')                   # have R functions print out fractional seconds


###   Helper functions ---------------------------------------------------------


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
            r_args.append(ri.MissingArg)
        elif isinstance(arg,newint):
            ###r_args.append(R_integer(arg))
            r_args.append(arg)
        else:
            r_args.append(arg)
            
    return tuple(r_args)

    
def _R_radiusArgs(latitude, longitude, minradius, maxradius):
    """
    Several webservices support location-radius arguments.
    
    Make sure that if any of these are defined then lat, lon
    and at least one of the radii are defined. Then, convert
    any None values to `rpy2.rinterface.MissingArg`.
    """
    if any([latitude,longitude,minradius,maxradius]):
        if all([latitude,longitude]) and any([minradius,maxradius]):
            # TODO:  Could add domain validation of values at this point
            if minradius is None:
                minradius = ri.MissingArg
            elif maxradius is None:
                maxradius = ri.MissingArg
            return (latitude, longitude, minradius, maxradius)
        else:
            raise ValueError("One of longitude, latitude or a radius is missing")
    else:
        return (ri.MissingArg, ri.MissingArg, ri.MissingArg, ri.MissingArg)



###   R functions called internally     ----------------------------------------


# NOTE:  These functions behave exactly the same as the R versions and require
# NOTE:  R-compatible objects as arguments.

# All webservice functions from IRISSeismic
_R_getAvailability = r('IRISSeismic::getAvailability')       #
_R_getChannel = r('IRISSeismic::getChannel')                 #
_R_getDataselect = r('IRISSeismic::getDataselect')           # TODO:  Same as getSNCL
_R_getDistaz = r('IRISSeismic::getDistaz')                   #
_R_getEvalresp = r('IRISSeismic::getEvalresp')               #
_R_getEvent = r('IRISSeismic::getEvent')                     #
_R_getNetwork = r('IRISSeismic::getNetwork')                 #
_R_getRotation = r('IRISSeismic::getRotation')               # TODO:  This returns 3 Streams
_R_getSNCL = r('IRISSeismic::getSNCL')                       #
_R_getStation = r('IRISSeismic::getStation')                 #
_R_getTraveltime = r('IRISSeismic::getTraveltime')           #
_R_getUnavailability = r('IRISSeismic::getUnavailability')   #


###   Python wrappers for R get~ webservice functions     ----------------------


def getAvailability(sncl, starttime, endtime,
                    latitude=None, longitude=None,
                    minradius=None, maxradius=None):
    """
    Returns a dataframe with channel metadata.
    :param sncl: SNCL (e.g. "US.OXF..BHZ")
    :param starttime: ObsPy UTCDateTime object.
    :param endtime: ObsPy UTCDateTime object.
    :param latitude: Optional latitude used when specifying a location and radius.
    :param longitude: Optional longitude used when specifying a location and radius.
    :param minradius: Optional minimum radius used when specifying a location and radius.
    :param maxradius: Optional maximum radius used when specifying a location and radius.
    :return: Pandas dataframe of channel metadata.
    """
    # Create/validate all arguments that can be accepted by the IRISSeismic::getAvailability() function
    r_client = r('new("IrisClient")')
    (network, station, location, channel) = sncl.split('.')
    starttime = R_POSIXct(starttime)
    endtime = R_POSIXct(endtime)
    includerestricted = ri.MissingArg  # NOTE:  IRIS DMC restricted datasets are not supported
    (latitude, longitude, minradius, maxradius) = _R_radiusArgs(latitude, longitude, minradius, maxradius)
    
    # Call the function and return a Pandas dataframe with the results
    r_df = _R_getAvailability(r_client, network, station, location, channel, starttime, endtime, includerestricted,
                              latitude, longitude, minradius, maxradius)
    df = pandas2ri.ri2py(r_df)
    return df
    
    
def getChannel(sncl, starttime, endtime,
               latitude=None, longitude=None,
               minradius=None, maxradius=None):
    """
    Returns a dataframe with channel metadata.
    :param sncl: SNCL (e.g. "US.OXF..BHZ")
    :param starttime: ObsPy UTCDateTime object.
    :param endtime: ObsPy UTCDateTime object.
    :param latitude: Optional latitude used when specifying a location and radius.
    :param longitude: Optional longitude used when specifying a location and radius.
    :param minradius: Optional minimum radius used when specifying a location and radius.
    :param maxradius: Optional maximum radius used when specifying a location and radius.
    :return: Pandas dataframe of channel metadata.
    """
    # Create/validate all arguments that can be accepted by the IRISSeismic::getAvailability() function
    r_client = r('new("IrisClient")')
    (network, station, location, channel) = sncl.split('.')
    starttime = R_POSIXct(starttime)
    endtime = R_POSIXct(endtime)
    includerestricted = ri.MissingArg # NOTE:  IRIS DMC restricted datasets are not supported
    (latitude,longitude,minradius,maxradius) = _R_radiusArgs(latitude, longitude, minradius, maxradius)
    
    # Call the function and return a Pandas dataframe with the results
    r_df = _R_getChannel(r_client, network, station, location, channel, starttime, endtime, includerestricted, latitude, longitude, minradius, maxradius)
    df = pandas2ri.ri2py(r_df)
    return df
    
    
def getDistaz(latitude, longitude, staLatitude, staLongitude):
    """
    Returns a dataframe with great circle distance data from the IRIS DMC distaz webservice.
    :param latitude: Latitude of seismic event.
    :param longitude: Longitude of seismic event.
    :param staLatitude: Latitude of seismic station.
    :param staLongitude: Longitude of seismic station.
    :return: Pandas dataframe with a single row containing ``azimuth, backAzimuth, distance``.
    """
    # Create/validate all arguments that can be accepted by the IRISSeismic::getAvailability() function
    r_client = r('new("IrisClient")')
    
    # Call the function and return a Pandas dataframe with the results
    r_df = _R_getDistaz(latitude, longitude, staLatitude, staLongitude)
    df = pandas2ri.ri2py(r_df)
    return df
    

def getEvalresp(sncl, time,
                minfreq=None, maxfreq=None,
                nfreq=None, units=None, output="fap"):
    """
    Returns a dataframe with cinstrument response data from the IRIS DMC evalresp webservice.
    :param sncl: SNCL (e.g. "US.OXF..BHZ")
    :param time: ObsPy UTCDateTime object specifying the time at which the response is evaluated.
    :param minfreq: Optional minimum frequency at which the response is evaluated.
    :param maxfreq: Optional maximum frequency at which the response is evaluated.
    :param nfreq: Optional number of frequencies at which response will be evaluated.
    :param units: Optional code specifying unit conversion.
    :param output: Output type ['fap'|'cs'].
    :return: Pandas dataframe of response metadata.
    """
    # Create/validate all arguments that can be accepted by the IRISSeismic::getAvailability() function
    r_client = r('new("IrisClient")')
    (network, station, location, channel) = sncl.split('.')
    time = R_POSIXct(time)
    (minfreq, maxfreq, nfreq, units, output) = _R_args(minfreq, maxfreq, nfreq, units, output)

    # Call the function and return a Pandas dataframe with the results
    r_df = _R_getEvalresp(r_client, network, station, location, channel, time, minfreq, maxfreq, nfreq, units, output)
    df = pandas2ri.ri2py(r_df)
    return df
    
    
def getEvent(starttime, endtime,
             minmag=None, maxmag=None, magtype=None,
             mindepth=None, maxdepth=None):
    """
    Returns a dataframe with channel metadata.
    :param starttime: ObsPy UTCDateTime object.
    :param endtime: ObsPy UTCDateTime object.
    :param minmag: Optional minimum magnitude.
    :param maxmag: Optional maximum magnitude.
    :param magtype:Optional magnitude type
    :param mindepth: Optional minimum depth (km).
    :param maxdepth: ptional maximum depth (km).
    :return: Pandas dataframe of event metadata.
    
    .. rubric:: Example
    
    >>> df = getEvent(UTCDateTime("2012-06-21"),UTCDateTime("2012-06-28"),minmag=6)
    >>> df.shape
    (2, 13)
    >>> df.eventLocationName
    0    NORTHERN SUMATERA, INDONESIA
    1    NEAR EAST COAST OF KAMCHATKA
    Name: eventLocationName, dtype: object
    """
    # Create/validate all arguments that can be accepted by the IRISSeismic::getAvailability() function
    r_client = r('new("IrisClient")')
    starttime = R_POSIXct(starttime)
    endtime = R_POSIXct(endtime)
    (minmag, maxmag, magtype, mindepth, maxdepth) = _R_args(minmag, maxmag, magtype, mindepth, maxdepth)
    
    # Call the function and return a Pandas dataframe with the results
    r_df = _R_getEvent(r_client, starttime, endtime, minmag, maxmag, magtype, mindepth, maxdepth)
    df = pandas2ri.ri2py(r_df)
    return df
        
    
def getNetwork(sncl, starttime, endtime,
               latitude=None, longitude=None,
               minradius=None, maxradius=None):
    """
    Returns a dataframe with network metadata.
    :param sncl: SNCL (e.g. "US.OXF..BHZ")
    :param starttime: ObsPy UTCDateTime object.
    :param endtime: ObsPy UTCDateTime object.
    :param latitude: Optional latitude used when specifying a location and radius.
    :param longitude: Optional longitude used when specifying a location and radius.
    :param minradius: Optional minimum radius used when specifying a location and radius.
    :param maxradius: Optional maximum radius used when specifying a location and radius.
    :return: Pandas dataframe of network metadata.
    """
    # Create/validate all arguments that can be accepted by the IRISSeismic::getAvailability() function
    r_client = r('new("IrisClient")')
    (network, station, location, channel) = sncl.split('.')
    starttime = R_POSIXct(starttime)
    endtime = R_POSIXct(endtime)
    includerestricted = ri.MissingArg # NOTE:  IRIS DMC restricted datasets are not supported
    (latitude,longitude,minradius,maxradius) = _R_radiusArgs(latitude, longitude, minradius, maxradius)
    
    # Call the function and return a Pandas dataframe with the results
    r_df = _R_getNetwork(r_client, network, station, location, channel, starttime, endtime, includerestricted, latitude, longitude, minradius, maxradius)
    df = pandas2ri.ri2py(r_df)
    return df
    
    
def R_getSNCL(sncl, starttime, endtime,
              quality=None):
    """
    Obtain an R Stream using the IRISSeismic::getSNCL function.
    :param sncl: SNCL (e.g. "US.OXF..BHZ")
    :param starttime: ObsPy UTCDateTime object.
    :param endtime: ObsPy UTCDateTime object.
    :return: R Stream object
    """
    r_client = r('new("IrisClient")')
    starttime = R_POSIXct(starttime)
    endtime = R_POSIXct(endtime)
    if quality is None:
        quality = ri.MissingArg
    r_stream = _R_getSNCL(r_client, sncl, starttime, endtime, quality)
    return r_stream
    
    
def getStation(sncl, starttime, endtime,
               latitude=None, longitude=None,
               minradius=None, maxradius=None):
    """
    Returns a dataframe with station metadata.
    :param sncl: SNCL (e.g. "US.OXF..BHZ")
    :param starttime: ObsPy UTCDateTime object.
    :param endtime: ObsPy UTCDateTime object.
    :param latitude: Optional latitude used when specifying a location and radius.
    :param longitude: Optional longitude used when specifying a location and radius.
    :param minradius: Optional minimum radius used when specifying a location and radius.
    :param maxradius: Optional maximum radius used when specifying a location and radius.
    :return: Pandas dataframe of channel metadata.
    """
    # Create/validate all arguments that can be accepted by the IRISSeismic::getAvailability() function
    r_client = r('new("IrisClient")')
    (network, station, location, channel) = sncl.split('.')
    starttime = R_POSIXct(starttime)
    endtime = R_POSIXct(endtime)
    includerestricted = ri.MissingArg # NOTE:  IRIS DMC restricted datasets are not supported
    (latitude,longitude,minradius,maxradius) = _R_radiusArgs(latitude, longitude, minradius, maxradius)
    
    # Call the function and return a Pandas dataframe with the results
    r_df = _R_getStation(r_client, network, station, location, channel, starttime, endtime, includerestricted, latitude, longitude, minradius, maxradius)
    df = pandas2ri.ri2py(r_df)
    return df


def getTraveltime(latitude, longitude, depth, staLatitude, staLongitude):
    """
    Returns a dataframe with seismic traveltime data from the IRIS DMC traveltime web service.
    :param latitude: Latitude of seismic event.
    :param longitude: Longitude of seismic event.
    :param staLatitude: Latitude of seismic station.
    :param staLongitude: Longitude of seismic station.
    :return: Pandas dataframe with coluns: ``distance, depth, phaseName, travelTime, rayParam, takeoff, incident, puristDistance, puristName``.
    """
    # Create/validate all arguments that can be accepted by the IRISSeismic::getAvailability() function
    r_client = r('new("IrisClient")')
    
    # Call the function and return a Pandas dataframe with the results
    r_df = _R_getTraveltime(r_client, latitude, longitude, depth, staLatitude, staLongitude)
    df = pandas2ri.ri2py(r_df)
    return df
    
    
def getUnavailability(sncl, starttime, endtime,
                      latitude=None, longitude=None,
                      minradius=None, maxradius=None):
    """
    Returns a dataframe with channel metadata for non-available channels.
    :param sncl: SNCL (e.g. "US.OXF..BHZ")
    :param starttime: ObsPy UTCDateTime object.
    :param endtime: ObsPy UTCDateTime object.
    :param latitude: Optional latitude used when specifying a location and radius.
    :param longitude: Optional longitude used when specifying a location and radius.
    :param minradius: Optional minimum radius used when specifying a location and radius.
    :param maxradius: Optional maximum radius used when specifying a location and radius.
    :return: Pandas dataframe of channel metadata.
    """
    # Create/validate all arguments that can be accepted by the IRISSeismic::getAvailability() function
    r_client = r('new("IrisClient")')
    (network, station, location, channel) = sncl.split('.')
    starttime = R_POSIXct(starttime)
    endtime = R_POSIXct(endtime)
    includerestricted = ri.MissingArg # NOTE:  IRIS DMC restricted datasets are not supported
    (latitude,longitude,minradius,maxradius) = _R_radiusArgs(latitude, longitude, minradius, maxradius)
    
    # Call the function and return a Pandas dataframe with the results
    r_df = _R_getUnvailability(r_client, network, station, location, channel, starttime, endtime, includerestricted, latitude, longitude, minradius, maxradius)
    df = pandas2ri.ri2py(r_df)
    return df


### ----------------------------------------------------------------------------


if __name__ == '__main__':
    import doctest
    doctest.testmod(exclude_empty=True)
