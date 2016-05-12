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

import math
import pandas as pd

import utils
import irisseismic
import irismustangmetrics


def PSD_metrics(concierge):
    """
    Generate *PSD* metrics.

    :type concierge: :class:`~ispaq.concierge.Concierge`
    :param concierge: Data access expiditer.
    
    :rtype: pandas dataframe (TODO: change this)
    :return: Dataframe of PSD metrics. (TODO: change this)

    .. rubric:: Example

    TODO:  doctest examples
    """
    # Get the logger from the concierge
    logger = concierge.logger
    
    # Container for all of the metrics dataframes generated
    dataframes = []

    # ----- All UN-available SNCLs ----------------------------------------------

    # TODO:  Anything to do here?

    # ----- All available SNCLs -------------------------------------------------
    
    availability = concierge.get_availability()

    # function metadata dictionary
    PSD_function_meta = concierge.function_by_logic['PSD']
    
    # Loop over rows of the availability dataframe
    for (index, av) in availability.iterrows():
                
        logger.info('Calculating PSD metrics for ' + av.snclId)

        # Get the data ----------------------------------------------

        # NOTE:  Use the requested starttime, not just what is available
        try:
            r_stream = concierge.get_dataselect(av.network, av.station, av.location, av.channel)
        except Exception as e:
            logger.warning('Unable to obtain data for %s: %s' % (av.snclId, concierge.dataselect_url, e))
            # TODO:  Add empty dataframe ???
            #df = pd.DataFrame({'metricName': 'percent_available',
                               #'value': 0,
                               #'snclq': av.snclId + '.M',
                               #'starttime': concierge.requested_starttime,
                               #'endtime': concierge.requested_endtime,
                               #'qualityFlag': -9},
                              #index=[0]) 
            #dataframes.append(df)
            continue


        # Run the PSD metric ----------------------------------------

        try:
            df = irismustangmetrics.apply_PSD_metric(r_stream)
            dataframes.append(df)
        except Exception as e:
            logger.error('ERROR in "PSD" metric calculation for %s: %s' % (av.snclId, e))
                

    # Concatenate and filter dataframes before returning -----------------------
                
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
