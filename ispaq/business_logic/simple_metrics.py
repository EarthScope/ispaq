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
import ispaq.concierge.utils as utils

from ispaq.irisseismic.webservices import R_getSNCL

from ispaq.irismustangmetrics import apply_simple_metric

import math

import pandas as pd


def simple_metrics(concierge, verbose=False):
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

    # TODO:  Create percent_availability metric with   0% available

    # ----- All available SNCLs -------------------------------------------------
    
    availability = concierge.get_availability()

    # function metadata dictionary
    simple_function_meta = concierge.function_by_logic['simple']
    
    # Loop over rows of the availability dataframe
    for (index, av) in availability.iterrows():
                
        if verbose: print('Calculating simple metrics for ' + av.snclId)

        # Get the data ----------------------------------------------

        # NOTE:  Use the requested starttime, not just what is available
        try:
            r_stream = R_getSNCL(concierge.dataselect_url, av.snclId, concierge.requested_starttime, concierge.requested_endtime)
        except Exception as e:
            if verbose: print('\n*** Unable to obtain data for %s from %s ***\n' % (av.snclId, concierge.dataselect_url))
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

        if simple_function_meta.has_key('gaps'):
            try:
                df = apply_simple_metric(r_stream, 'gaps')
                dataframes.append(df)
            except Exception as e:
                if verbose: print('\n*** ERROR in "gaps" metric calculation for %s ***\n' % (av.snclId))
                
                
        # Run the State-of-Health metric -----------------------------

        if simple_function_meta.has_key('stateOfHealth'):
            try:
                df = apply_simple_metric(r_stream, 'stateOfHealth')
                dataframes.append(df)
            except Exception as e:
                if verbose: print('\n*** ERROR in "stateOfHealth" metric calculation for %s ***\n' % (av.snclId))
                            
            
        # Run the Basic Stats metric ---------------------------------

        if simple_function_meta.has_key('basicStats'):
            try:
                df = apply_simple_metric(r_stream, 'basicStats')
                dataframes.append(df)
            except Exception as e:
                if verbose: print('\n*** ERROR in "basicStats" metric calculation for %s ***\n' % (av.snclId))
                            
       
        # Run the STALTA metric --------------------------------------
       
        # NOTE:  To improve performance, we do not calculate STA/LTA at every single point in 
        # NOTE:  high resolution data.  Instead, we calculate STA/LTA at one point and then skip
        # NOTE:  ahead a few points as determined by the "increment" parameter.
        # NOTE:  An increment that translates to 0.2-0.5 secs seems to be a good compromise
        # NOTE:  between performance and accuracy.
    
        if simple_function_meta.has_key('STALTA'):
            
            # Limit this metric to BH. and HH. channels
            if av.channel.startswith('BH') or av.channel.startswith('HH'):
                sampling_rate = utils.get_slot(r_stream, 'sampling_rate')
                increment = math.ceil(sampling_rate/2)
                
                try:
                    df = apply_simple_metric(r_stream, 'STALTA', staSecs=3, ltaSecs=30, increment=increment, algorithm='classic_LR')
                    dataframes.append(df)
                except Exception as e:
                    if verbose: print('\n*** ERROR in "STALTA" metric calculation for %s ***\n' % (av.snclId))
            
            
        # Run the Spikes metric --------------------------------------

        # NOTE:  Appropriate values for spikesMetric arguments are determined empirically
            
        if simple_function_meta.has_key('spikes'):
       
            windowSize = 41
            thresholdMin = 7
            selectivity = 0.5
       
            # Lower resolution channels L.. need a higher thresholdMin
            sampling_rate = utils.get_slot(r_stream, 'sampling_rate')
            if sampling_rate >= 1:
                thresholdMin = 12
    
            try:
                df = apply_simple_metric(r_stream, 'spikes', windowSize, thresholdMin, selectivity)
                dataframes.append(df)
            except Exception as e:
                if verbose: print('\n*** ERROR in "spikes" metric calculation for %s ***\n' % (av.snclId))            
                

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