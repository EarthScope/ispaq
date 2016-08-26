"""
ISPAQ Business Logic for Simple Metrics.

:copyright:
    Mazama Science
:license:
    GNU Lesser General Public License, Version 3
    (http://www.gnu.org/copyleft/lesser.html)
"""

from __future__ import (absolute_import, division, print_function)

import math
import numpy as np
import pandas as pd

from obspy import UTCDateTime

from . import utils
from . import irisseismic
from . import irismustangmetrics


def simple_metrics(concierge):
    """
    Generate *simple* metrics.

    :type concierge: :class:`~ispaq.concierge.Concierge`
    :param concierge: Data access expiditer.
    
    :rtype: pandas dataframe
    :return: Dataframe of simple metrics.

    .. rubric:: Example

    TODO:  doctest examples
    """
    # Get the logger from the concierge
    logger = concierge.logger
    
    # Container for all of the metrics dataframes generated
    dataframes = []

    # ----- All UN-available SNCLs ----------------------------------------------

    # TODO:  Create percent_availability metric with   0% available

    # ----- All available SNCLs -------------------------------------------------
    
    availability = concierge.get_availability()

    # function metadata dictionary
    function_metadata = concierge.function_by_logic['simple']
    
    logger.info('Calculating simple metrics for %d SNCLs.' % (availability.shape[0]))
    
    # Loop over rows of the availability dataframe
    for (index, av) in availability.iterrows():
                
        logger.info('%03d Calculating simple metrics for %s' % (index, av.snclId))

        # Get the data ----------------------------------------------

        # NOTE:  Use the requested starttime, not just what is available
        try:
            r_stream = concierge.get_dataselect(av.network, av.station, av.location, av.channel)
        except Exception as e:
            if str(e).lower().find('no data') > -1:
                logger.debug('No data for %s' % (av.snclId))
            else:
                logger.debug('No data for %s from %s: %s' % (av.snclId, concierge.dataselect_url, e))
            df = pd.DataFrame({'metricName': 'percent_available',
                               'value': 0,
                               'snclq': av.snclId + '.M',
                               'starttime': concierge.requested_starttime,
                               'endtime': concierge.requested_endtime,
                               'qualityFlag': -9},
                              index=[0]) 
            dataframes.append(df)
            continue

        # Run the Gaps metric ----------------------------------------

        if function_metadata.has_key('gaps'):
            try:
                df = irismustangmetrics.apply_simple_metric(r_stream, 'gaps')
                dataframes.append(df)
            except Exception as e:
                logger.debug('"gaps" metric calculation failed for %s: %s' % (av.snclId, e))
                
                
        # Run the State-of-Health metric -----------------------------

        if function_metadata.has_key('stateOfHealth'):
            try:
                df = irismustangmetrics.apply_simple_metric(r_stream, 'stateOfHealth')
                dataframes.append(df)
            except Exception as e:
                logger.debug('"stateOfHealth" metric calculation failed for %s: %s' % (av.snclId, e))
                            
            
        # Run the Basic Stats metric ---------------------------------

        if function_metadata.has_key('basicStats'):
            try:
                df = irismustangmetrics.apply_simple_metric(r_stream, 'basicStats')
                dataframes.append(df)
            except Exception as e:
                logger.debug('"basicStats" metric calculation failed for %s: %s' % (av.snclId, e))
                            
       
        # Run the STALTA metric --------------------------------------
       
        # NOTE:  To improve performance, we do not calculate STA/LTA at every single point in 
        # NOTE:  high resolution data.  Instead, we calculate STA/LTA at one point and then skip
        # NOTE:  ahead a few points as determined by the "increment" parameter.
        # NOTE:  An increment that translates to 0.2-0.5 secs seems to be a good compromise
        # NOTE:  between performance and accuracy.
    
        if function_metadata.has_key('STALTA'):
            
            # Limit this metric to BH. and HH. channels
            if av.channel.startswith('BH') or av.channel.startswith('HH'):
                sampling_rate = utils.get_slot(r_stream, 'sampling_rate')
                increment = math.ceil(sampling_rate/2.0)
                
                try:
                    df = irismustangmetrics.apply_simple_metric(r_stream, 'STALTA', staSecs=3, ltaSecs=30, increment=increment, algorithm='classic_LR')
                    dataframes.append(df)
                except Exception as e:
                    logger.debug('"STALTA" metric calculation failed for for %s: %s' % (av.snclId, e))
            
            
        # Run the Spikes metric --------------------------------------

        # NOTE:  Appropriate values for spikesMetric arguments are determined empirically
            
        if function_metadata.has_key('spikes'):
       
            # Limit this metric to BH. and HH. channels
            if av.channel.startswith('BH') or av.channel.startswith('HH'):
                windowSize = 41
                thresholdMin = 10
                   
                try:
                    df = irismustangmetrics.apply_simple_metric(r_stream, 'spikes', windowSize, thresholdMin, fixedThreshold=True)
                    dataframes.append(df)
                except Exception as e:
                    logger.debug('"spikes" metric calculation failed for %s: %s' % (av.snclId, e))            
                

    # Concatenate and filter dataframes before returning -----------------------
    
    # Create a boolean mask for filtering the dataframe
    def valid_metric(x):
        return x in concierge.metric_names
        
    if len(dataframes) == 0:
        logger.warn('"simple" metric calculation generated zero metrics')
        return None
    else:
        result = pd.concat(dataframes, ignore_index=True)    
        mask = result.metricName.apply(valid_metric)
        result = result[(mask)]
        result.reset_index(drop=True, inplace=True)        
        return(result)


# ------------------------------------------------------------------------------


if __name__ == '__main__':
    import doctest
    doctest.testmod(exclude_empty=True)
