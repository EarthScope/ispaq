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

from ispaq.concierge.concierge import Concierge

from ispaq.irisseismic.webservices import *

from ispaq.irismustangmetrics import *


import pandas as pd


def generate_simple_metrics(concierge, verbose=False):
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
    dataframes = []

    # ----- All UN-available SNCLs ----------------------------------------------



    # ----- All available SNCLs -------------------------------------------------
    

    # function metadata dictionary
    simple_function_meta = concierge.function_by_logic['simple']
    
    # loop over available SNCLS
    for sncl in concierge.get_sncls():
        print('Calculating simple metrics for ' + sncl)

        # Get the data ----------------------------------------------

        # NOTE:  Use the requested starttime, not just what is available
        r_stream = R_getSNCL(concierge.dataselect_url, sncl, concierge.requested_starttime, concierge.requested_endtime)

        # Calculate the metrics -------------------------------------

        for function_name in simple_function_meta.keys():
            function_meta = simple_function_meta[function_name]

            # Special logic for Spikes metric -----------------------

            if 'num_spikes' in function_meta['metrics']:
                print('special logic required for num_spikes metric with ' + function_name + ' function')
                # TODO:  special logic for num_spikes

            else:
                print('    ' + function_name + ' will calculate ' + str(function_meta['metrics']))
                df = applySimpleMetric(r_stream, function_name)
                dataframes.append(df)

    # Concatenate all data frames
    # TODO:  Check to guarantee that columns will ALWAYS be the same
    result = pd.concat(dataframes)
    
    # Filter the full dataframe ------------------------------------------------
    
    # Create a boolean mask for filtering the dataframe
    def valid_metric(x):
        return x in concierge.metric_names
        
    mask = result.metricName.apply(valid_metric)
    result = result[(mask)]
    
    return(result)


if __name__ == '__main__':
    import doctest
    doctest.testmod(exclude_empty=True)