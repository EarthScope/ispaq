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

# R options
r('options(digits.secs=6)')                   # have R functions print out fractional seconds



###   R functions called internally     ----------------------------------------


# NOTE:  These functions behave exactly the same as the R versions and require
# NOTE:  R-compatible objects as arguments.[]

# All webservice functions from IRISSeismic
_R_getAvailability = r('IRISSeismic::getAvailability')
_R_getChannel = r('IRISSeismic::getChannel')
_R_getDataselect = r('IRISSeismic::getDataselect')
_R_getDistaz = r('IRISSeismic::getDistaz')
_R_getEvalresp = r('IRISSeismic::getEvalresp')
_R_getEvent = r('IRISSeismic::getEvent')
_R_getNetwork = r('IRISSeismic::getNetwork')
_R_getRotation = r('IRISSeismic::getRotation')
_R_getSNCL = r('IRISSeismic::getSNCL')
_R_getStation = r('IRISSeismic::getStation')
_R_getTraveltime = r('IRISSeismic::getTraveltime')
_R_getUnavailability = r('IRISSeismic::getUnavailability')


###   Python wrappers for R get~ webservice functions     ----------------------


def getChannel(sncl, starttime, endtime):
    """
    Returns a dataframe with channel metadata.
    :param sncl: SNCL (e.g. "US.OXF..BHZ")
    :param starttime: ObsPy UTCDateTime object.
    :param endtime: ObsPy UTCDateTime object.
    :return: R Stream object
    """
    r_client = r('new("IrisClient")')
    (network, station, location, channel) = sncl.split('.')
    starttime = R_POSIXct(starttime)
    endtime = R_POSIXct(endtime)
    r_df = _R_getChannel(r_client, network, station, location, channel, starttime, endtime) # NOTE:  Accepting R function defaults for additional parameters
    df = pandas2ri.ri2py(r_df)
    return(df)
    
    
def R_getSNCL(sncl, starttime, endtime):
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
    r_stream = _R_getSNCL(r_client, sncl, starttime, endtime) # NOTE:  Accepting R function default for final "quality" argument.
    return(r_stream)
    
    

### ----------------------------------------------------------------------------


if __name__ == '__main__':
    import doctest
    doctest.testmod(exclude_empty=True)
