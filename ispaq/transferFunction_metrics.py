"""
ISPAQ Business Logic for transfer Metrics.

:copyright:
    Mazama Science
:license:
    GNU Lesser General Public License, Version 3
    (http://www.gnu.org/copyleft/lesser.html)
"""
from obspy import UTCDateTime
from obspy.clients.fdsn import Client

import math
import numpy as np
import pandas as pd

import utils
import irisseismic
import irismustangmetrics

def transferFunction_metrics(concierge):
    """
    Generate *transfer* metrics.

    :type concierge: :class:`~ispaq.concierge.Concierge`
    :param concierge: Data access expiditer.

    :rtype: pandas dataframe
    :return: Dataframe of simple metrics.

    .. rubric:: Example

    TODO:  doctest examples
    """
    # Get the logger from the concierge
    logger = concierge.logger

    # TODO Finish function

    # Create a boolean mask for filtering the dataframe
    def valid_metric(x):
        return x in concierge.metric_names

    result = pd.concat(dataframes, ignore_index=True)
    mask = result.metricName.apply(valid_metric)
    result = result[(mask)]
    result.reset_index(drop=True, inplace=True)

    return(result)


# ------------------------------------------------------------------------------


if __name__ == '__main__':
    import doctest
    doctest.testmod(exclude_empty=True)
