# -*- coding: utf-8 -*-
"""
ispaq.concierge - ISPAQ Data Access Expediter
======================================================
The ispaq.concierge package provides a simplified data access API for many
FDSN and IRIS web services.

:copyright:
    Mazama Science
:license:
    GNU Lesser General Public License, Version 3
    (http://www.gnu.org/copyleft/lesser.html)

The concierge is initialized with a completely filled out `user_request`
and has the job of expediting requests for information that may be made
by any of the business_logic methods.

The goal is to have business_logic methods that can be written as 
similarly to the original R code as possible without having to know about
the intricacies of ObsPy. Thus, the concierge provides methods like

`concierge.get_availability()`

which returns a pandas dataframe with the same information that is 
returned by the `IRISSeismic::getAvailability()` function

It is assumed that all of the information required as input to 
`get_availability`, e.g. [starttime, endtime, sncl_patterns, client_url, ...]
are part of the `user_request` object that the concierge has access to
"""
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
from future.builtins import *  # NOQA
from future.utils import native_str

from ispaq.business_logic.simple_metrics import generate_simple_metrics


if __name__ == '__main__':
    import doctest
    doctest.testmod(exclude_empty=True)
