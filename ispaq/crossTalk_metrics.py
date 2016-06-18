"""
ISPAQ Business Logic for Cross-Talk Metrics.

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


def crossTalk_metrics(concierge):
    """
    Generate *crossTalk* metrics.

    :type concierge: :class:`~ispaq.concierge.Concierge`
    :param concierge: Data access expiditer.
    
    :rtype: pandas dataframe
    :return: Dataframe of simple metrics.

    .. rubric:: Example

    TODO:  doctest examples
    """
    # Get the logger from the concierge
    logger = concierge.logger
        
    # Default parameters from IRISMustangUtils::generateMetrics_crossTalk
    minmag = 5.5
    maxradius = 180
    windowSecs = 60
        
    # Get the seismic events in this time period
    events = concierge.get_event(minmag=minmag)
        
    # Sanity check
    if events is None or events.shape[0] == 0:
        logger.info('No events found for crossTalk metrics.')
        return None
        
    # Container for all of the metrics dataframes generated
    dataframes = []

    #############################################################
    ## Loop through each event.
    #############################################################


    logger.info('Calculating crossTalk metrics for %d events' % events.shape[0])

    for (index, event) in events.iterrows():

        logger.info('%03d Magnitude %3.1f event: %s' % (index, event.magnitude, event.eventLocationName))
        
        # Sanity check
        if pd.isnull(event.latitude) or pd.isnull(event.longitude):
            logger.debug('Skipping event because of missing longitude or latitude')
            continue
    
        # Sanity check
        if pd.isnull(event.depth):
            logger.debug('Skipping event because of missing depth')
            continue        
        
        # Get the data availability around this event
        # NOTE:  Get availability from 2 minutes before event until 28 minutes after
        # Get the data availability using spatial search parameters
        halfHourStart = event.time - 60 * 2
        halfHourEnd = event.time + 60 * 28

        try:        
            availability = concierge.get_availability(starttime=halfHourStart, endtime=halfHourEnd,
                                                      longitude=event.longitude, latitude=event.latitude,
                                                      minradius=0, maxradius=maxradius)
        except Exception as e:
            logger.debug('Skipping event because get_availability failed: %s' % (e))
            continue
                    
        # Sanity check that some SNCLs exist
        if availability.shape[0] == 0:
            logger.debug('Skipping event because no SNCLs are available')
            continue
    
        # Channel types (as opposed to orientation) will contain only the first two characters
        channelType = availability.channel.apply(lambda x: x[0:2])

        # Find unique network-station-location combinations
        sn_lIds = availability.network + '.' + availability.station + '.' + availability.location + '.' + channelType
        
        # Add sn_lId to the availability dataframe for easy detection
        availability['sn_lId'] = sn_lIds

        # ----- All available SNCLs -------------------------------------------------

        for sn_lId in sorted(list(set(sn_lIds))):

            logger.debug('Working on SN.L %s' % (sn_lId))

            availabilitySub = availability[availability.sn_lId == sn_lId]
            
            if availabilitySub.shape[0] == 1:
                logger.debug('Skipping %s because there is only a single channel at this SN.L' % (sn_lId))
                continue

            # Get the data --------------------------------------

            # NOTE:  Expand the window by an extra second to guarantee that 
            # NOTE:  halfHourStart < tr@stats@starttime and halfHourEnd > tr@stats@endtime
            streamList = []

            # Loop over rows of the availabilitySub dataframe
            for (index2, av) in availabilitySub.iterrows():
                            
                try:
                    r_stream = concierge.get_dataselect(av.network, av.station, av.location, av.channel, halfHourStart-1, halfHourEnd+1, inclusiveEnd=False)
                except Exception as e:
                    if str(e).lower().find('no data') > -1:
                        logger.debug('No data for %s' % (av.snclId))
                    else:
                        logger.debug('No data for %s from %s: %s' % (av.snclId, concierge.dataselect_url, e))
                    continue
                
                
                if len(utils.get_slot(r_stream, 'traces')) > 1 :
                    logger.debug('Skipping %s because it has more than one trace' % (av.snclId))
                    continue
                else:
                    streamList.append(r_stream)
                    
            if len(streamList) == 0:
                logger.debug('Skipping %s because it has no data' % (sn_lId))
                continue
                
            if len(streamList) == 1:
                logger.debug('Skipping %s because it only has data for one channel' % (sn_lId))
                continue   

            # Run the correlation metrics -----------------------

            # At this point, each stream in streamList has only one trace
            # and can now be used in the correlation metric.
            
            logger.debug('Calculating crossTalk metrics for %d streams.' % (len(streamList)))
            
            # 1-2
            try:
                df = irismustangmetrics.apply_correlation_metric(streamList[0], streamList[1], 'correlation')
                dataframes.append(df)
            except Exception as e:
                logger.debug('"crossTalk" metric calculation failed for %s: %s' % (av.snclId, e))
            
            if len(streamList) == 3:

                # 1-3
                try:
                    df = irismustangmetrics.apply_correlation_metric(streamList[0], streamList[2], 'correlation')
                    dataframes.append(df)
                except Exception as e:
                    logger.debug('"crossTalk" metric calculation failed for %s: %s' % (av.snclId, e))
                
                # 2-3
                try:
                    df = irismustangmetrics.apply_correlation_metric(streamList[1], streamList[2], 'correlation')
                    dataframes.append(df)
                except Exception as e:
                    logger.debug('"crossTalk" metric calculation failed for %s: %s' % (av.snclId, e))
                    

        # End of sn.lId loop

    # End of event loop

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
