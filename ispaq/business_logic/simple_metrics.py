"""
ISPAQ Business Logic for Simple Metrics.

:copyright:
    Mazama Science
:license:
    GNU Lesser General Public License, Version 3
    (http://www.gnu.org/copyleft/lesser.html)
"""
from obspy import UTCDateTime
from obspy.clients.fdsn import Client

import pandas as pd


def generate_simple_metrics(concierge):
    """
    Generate *simple* metrics.

    :type concierge: str
    :param concierge: Channel name, e.g. ``'BHZ'`` or ``'H'``
    :rtype: pandas dataframe
    :return: Dataframe of simple metrics.

    .. rubric:: Example

    TODO:  doctest examples
    """

    print(concierge)


if __name__ == '__main__':
    import doctest
    doctest.testmod(exclude_empty=True)