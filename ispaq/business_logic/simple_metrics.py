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

    :type concierge: :class:`~ispaq.concierge.Concierge`
    :param concierge: Data access expiditer.
    
    :rtype: pandas dataframe
    :return: Dataframe of simple metrics.

    .. rubric:: Example

    TODO:  doctest examples
    """

    # Container for all of the metrics dataframes generated
    metric_dfs = []

    # ----- All UN-available SNCLs ----------------------------------------------



    # ----- All available SNCLs -------------------------------------------------


    # loop over available SNCLS
    for sncl in concierge.get_sncls():
        print(sncl)

        # Get the data ----------------------------------------------

        # NOTE:  Use the requested starttime, not just what is available
        ###r_stream = R_getSNCL(sncl, starttime, endtime)

        # Calculate the metrics -------------------------------------

        for metric_set in concierge.simple_metric_sets:

            # Special logic for Spikes metric -----------------------

            if 'num_spikes' in simple_metrics:
                print('special logic for num_spikes')
                # TODO:  special logic for num_spikes

            else:
                print('calculating' + metric)
                # TODO:  calculate metric




if __name__ == '__main__':
    import doctest
    doctest.testmod(exclude_empty=True)