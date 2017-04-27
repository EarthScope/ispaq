"""
ISPAQ Business Logic for SNR Metrics.

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

from .concierge import NoAvailableDataError

from . import utils
from . import irisseismic
from . import irismustangmetrics


def SNR_metrics(concierge):
    """
    Generate *SNR* metrics.

    :type concierge: :class:`~ispaq.concierge.Concierge`
    :param concierge: Data access expiditer.
    
    :rtype: pandas dataframe
    :return: Dataframe of simple metrics.

    .. rubric:: Example

    TODO:  doctest examples
    """
    # Get the logger from the concierge
    logger = concierge.logger
        
    channelFilter = '.*'
    minmag = 5.5
    maxradius = 180
    windowSecs = 60
        
    # Get the seismic events in this time period
    events = concierge.get_event(minmag=minmag)
        
    # Sanity checck
    if events is None or events.shape[0] == 0:
        logger.info('No events found for SNR metrics')
        return None
        
    if concierge.station_url is None:
        logger.warning('No station metadata found for SNR metrics')
        return None

    # Container for all of the metrics dataframes generated
    dataframes = []

    #############################################################
    ## Loop through each event.
    #############################################################

    logger.info('Calculating SNR metrics for %d events.' % (events.shape[0]))

    for (index, event) in events.iterrows():
        logger.info('%03d Magnitude %3.1f Time %s event: %s' % (index, event.magnitude, event.time, event.eventLocationName))
        
        # Sanity check
        if pd.isnull(event.latitude) or pd.isnull(event.longitude):
            logger.info('Skipping event because of missing longitude or latitude')
            continue
    
        # Sanity check
        if pd.isnull(event.depth):
            logger.info('Skipping event because of missing depth')
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

        except NoAvailableDataError as e:
            logger.info('Skipping event with no available data')
            continue
        except Exception as e:            
            logger.warning('Skipping event because concierge.get_availability failed: %s' % (e))
            continue
        if availability is None:
            logger.info("Skipping event with no available data")
            continue
                    
        # Apply the channelFilter
        availability = availability[availability.channel.str.contains(channelFilter)]      

        # Sanity check that some SNCLs exist
        if availability.shape[0] == 0:
            logger.info('Skipping event with no available data')
            continue
        
        logger.debug('%d SNCLs available for this event' % (availability.shape[0]))        
    
    
        # ----- All available SNCLs -------------------------------------------------

        # function metadata dictionary
        function_metadata = concierge.function_by_logic['SNR']
    
        # Loop over rows of the availability dataframe
        for (index, av) in availability.iterrows():
            # if there is no metadata, then skip to the next row
            if math.isnan(av.latitude) or math.isnan(av.longitude):
                logger.debug("No metadata for " + av.snclId + ": skipping")
                continue

            # get the travel time between the event and the station
            try:
                tt = irisseismic.getTraveltime(event.latitude, event.longitude, event.depth, 
                                               av.latitude, av.longitude)
            except Exception as e:
                logger.warning('Skipping because getTravelTime failed: %s' % (e))
                continue
        
            # get P arrival or first arrival
            if not np.any(tt.phaseName == 'P'):
                travelTime = min(tt.travelTime)
            else:
                travelTime = min(tt.travelTime[tt.phaseName == 'P'])
                
            # For the arrival (P phase in some cases) minimum, define the SNR window
            windowStart = event.time + travelTime - windowSecs/2
            windowEnd = event.time + travelTime + windowSecs/2
                
            # Get the data
            # NOTE:  Exapand the window by an extra second to guarantee that 
            # NOTE:  windowStart < tr.stats.starttime and windowEnd > tr.stats.endtime
            try:
                r_stream = concierge.get_dataselect(av.network, av.station, av.location, av.channel, windowStart-1, windowEnd+1, inclusiveEnd=False)
            except Exception as e:
                if str(e).lower().find('no data') > -1:
                    logger.info('No data found for %s' % (av.snclId))
                else:
                    logger.warning('No data found for %s from %s: %s' % (av.snclId, concierge.dataselect_url, e))
                # TODO:  Create appropriate empty dataframe
                df = pd.DataFrame({'metricName': 'SNR',
                                   'value': 0,
                                   'snclq': av.snclId+'.M',
                                   'starttime': concierge.requested_starttime,
                                   'endtime': concierge.requested_endtime,
                                   'qualityFlag': -9},
                                  index=[0]) 
                dataframes.append(df)
                continue

            # Run the SNR metric
            if len(r_stream.do_slot('traces')) > 1:
                logger.info('Skipping %s because it has gaps' % (av.snclId)) 
                continue
            
            else:
                if (utils.get_slot(r_stream, 'starttime') > windowStart) or (utils.get_slot(r_stream,'endtime') < windowEnd):
                    logger.info('Skipping %s becuase it is missing data in the SNR window' % (av.snclId)) 
                    continue
                else:
                    logger.info('Calculating SNR metrics for %s' % (av.snclId))
                    try:
                        df = irismustangmetrics.apply_simple_metric(r_stream, 'SNR', algorithm="splitWindow", windowSecs=windowSecs)
                        dataframes.append(df)
                    except Exception as e:
                        logger.warning('"SNR" metric calculation failed for %s: %s' % (av.snclId, e))
                    
                

    # Concatenate and filter dataframes before returning -----------------------
    
    # Create a boolean mask for filtering the dataframe
    def valid_metric(x):
        return x in concierge.metric_names
        
    if len(dataframes) == 0:
        logger.warn('"SNR" metric calculation generated zero metrics')
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
