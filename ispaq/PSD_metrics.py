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

import os
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
    function_metadata = concierge.function_by_logic['PSD']
    
    # Loop over rows of the availability dataframe
    for (index, av) in availability.iterrows():
                
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

        if function_metadata.has_key('PSD'):
            logger.info('Calculating PSD metrics for ' + av.snclId)
            try:
                df = irismustangmetrics.apply_PSD_metric(r_stream)
                dataframes.append(df)
            except Exception as e:
                logger.error('ERROR in "PSD" metric calculation for %s: %s' % (av.snclId, e))
                
        # Run the PSD plot ------------------------------------------

        if function_metadata.has_key('PSDPlot'):
            logger.info('Generating PDF plot for ' + av.snclId)
            try:  
                # TODO:  Use concierge to determine where to put the plots?
                starttime = utils.get_slot(r_stream, 'starttime')
                filename = '%s.%s_PDF.png' % (av.snclId, starttime.strftime('%Y.%j'))
                filepath = os.getcwd() + '/' + filename
                status = irismustangmetrics.open_png_file(filepath)
                status = irismustangmetrics.apply_PSD_plot(r_stream)
            except Exception as e:
                logger.error('ERROR in "PSD" plot generation for %s: %s' % (av.snclId, e))
                    

    # Concatenate and filter dataframes before returning -----------------------

    # TODO:  Should we always add a dummy dataframe in cases where we only generate plots?
    result = pd.DataFrame({'metricName': 'DUMMY',
                           'value': 0,
                           'snclq': 'NET.STA.LOC.CHA.M',
                           'starttime': concierge.requested_starttime,
                           'endtime': concierge.requested_endtime,
                           'qualityFlag': -9},
                          index=[0]) 
    
    if function_metadata.has_key('PSD'):                    
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
