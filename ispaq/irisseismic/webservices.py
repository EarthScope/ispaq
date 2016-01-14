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

from ispaq.irisseismic.stream import *


### ----------------------------------------------------------------------------


# Connect to R through the rpy2 module
import rpy2.robjects as robjects
r = robjects.r

# R options
r('options(digits.secs=6)')                   # have R functions print out fractional seconds



###   R functions called internally     ----------------------------------------


# NOTE:  These functions behave exactly the same as the R versions and require
# NOTE:  R-compatible objects as arguments.

# from IRISSeismic
_R_getSNCL = r('IRISSeismic::getSNCL')        # to obtain an R_Stream object from IRIS DMC


###   Python wrappers for R get~ webservice functions     ----------------------


# NOTE:  ObsPy provides access to various IRIS webservices but these are returned
# NOTE:  as python objects. Here we utilize the IRISSeismic R package to obtain
# NOTE:  R objects which an be passed directly to the R metric functions.

def R_getSNCL(sncl, starttime, endtime):
    """
    Obtain an IRISSeismic Stream using the IRISSeismic::getSNCL function.
    :param sncl: SNCL (e.g. "US.OXF..BHZ")
    :param starttime: ObsPy UTCDateTime object.
    :param endtime: ObsPy UTCDateTime object.
    :return: IRISSeismic Stream object
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
