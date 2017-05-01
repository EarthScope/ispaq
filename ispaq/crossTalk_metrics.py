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

from .concierge import NoAvailableDataError

from . import utils
from . import irisseismic
from . import irismustangmetrics

pd.options.mode.chained_assignment = None
# chained_assignment added to skip "SettingWithCopyWarning: 
# A value is trying to be set on a copy of a slice from a DataFrame."
# for line 126: availability.loc[:,'sn_lId'] = sn_lIds 

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
        
    # Default parameters from IRISMustangUtils::generateMetrics_crossTalk or crossTalkMetrics_exec.R
    channelFilter = '[BH]H.'
    minmag = 5.5
    maxradius = 180
    windowSecs = 60
        
    # Sanity check for metadata
    if concierge.station_url is None:
        logger.warning('No station metadata found for crossTalk metrics')
        return None

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

        logger.info('%03d Magnitude %3.1f event: %s %s' % (index, event.magnitude, event.eventLocationName, event.time.strftime("%Y-%m-%dT%H:%M:%S")))
        
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
  
        logger.debug("Looking for metadata from %s to %s" % (halfHourStart.strftime("%Y-%m-%dT%H:%M:%S"),halfHourEnd.strftime("%Y-%m-%dT%H:%M:%S")))

        # crossTalk requires 3 channels, look for all 3 even if input SNCL pattern is for one (i.e., TA.109..BHZ will look for TA.109C..BH?)
        original_sncl_patterns = concierge.sncl_patterns
        new_sncl_patterns = []
        UR=["temp0","temp1","temp2","temp3"]
        for sncl_pattern in concierge.sncl_patterns:
            UR[concierge.netOrder] = sncl_pattern.split('.')[concierge.netOrder]
            UR[concierge.staOrder] = sncl_pattern.split('.')[concierge.staOrder]
            UR[concierge.locOrder] = sncl_pattern.split('.')[concierge.locOrder]
            UR[concierge.chanOrder] = sncl_pattern.split('.')[concierge.chanOrder]
            if len(UR[concierge.chanOrder]) == 3:
                UR[concierge.chanOrder]=UR[concierge.chanOrder][:-1] + '?'
            new_sncl_pattern = ".".join(UR)
            new_sncl_patterns.append(new_sncl_pattern)
        concierge.sncl_patterns = new_sncl_patterns    


        try:        
            availability = concierge.get_availability(starttime=halfHourStart, endtime=halfHourEnd,
                                                      longitude=event.longitude, latitude=event.latitude,
                                                      minradius=0, maxradius=maxradius)
        except NoAvailableDataError as e:
            logger.info('Skipping event with no available data')
            concierge.sncl_patterns = original_sncl_patterns
            continue
        except Exception as e:
            logger.warning('Skipping event because concierge.get_availability failed: %s' % (e))
            concierge.sncl_patterns = original_sncl_patterns
            continue
        if availability is None:
            logger.info("Skipping event with no available data")
            concierge.sncl_patterns = original_sncl_patterns
            continue

        concierge.sncl_patterns = original_sncl_patterns
                    
        # Apply the channelFilter
        availability = availability[availability.channel.str.contains(channelFilter)]      

        # Sanity check that some SNCLs exist
        if availability.shape[0] == 0:
            logger.info('Skipping event because no stations are available')
            continue
    
        # Channel types (as opposed to orientation) will contain only the first two characters
        channelType = availability.channel.apply(lambda x: x[0:2])

        # Find unique network-station-location combinations
        sn_lIds = availability.network + '.' + availability.station + '.' + availability.location + '.' + channelType
        
        # Add sn_lId to the availability dataframe for easy detection
        availability.loc[:,'sn_lId'] = sn_lIds

        # ----- All available SNCLs -------------------------------------------------

        for idx, sn_lId in enumerate(sorted(list(set(sn_lIds)))):

            logger.info('Calculating crossTalk metrics for %s' % (sn_lId))

            availabilitySub = availability[availability.sn_lId == sn_lId]
            
            if availabilitySub.shape[0] == 1:
                logger.info('Skipping %s because there is only a single channel at this SN.L' % (sn_lId))
                continue

            # Get the data --------------------------------------

            # NOTE:  Expand the window by an extra second to guarantee that 
            # NOTE:  halfHourStart < tr@stats@starttime and halfHourEnd > tr@stats@endtime
            streamList = []

            # Loop over rows of the availabilitySub dataframe
            for (index2, av) in availabilitySub.iterrows():

                # NEW if there is no metadata, then skip to the next row
                if math.isnan(av.latitude):
                    logger.info("No metadata for " + av.snclId + ": skipping")
                    continue                

                logger.debug("Looking for data for %s from %s to %s" % (av.snclId, halfHourStart.strftime("%Y-%m-%dT%H:%M:%S"), halfHourEnd.strftime("%Y-%m-%dT%H:%M:%S")))

                try:
                    r_stream = concierge.get_dataselect(av.network, av.station, av.location, av.channel, halfHourStart-1, halfHourEnd+1, inclusiveEnd=False)
                except Exception as e:
                    if str(e).lower().find('no data') > -1:
                        logger.info('No data available for %s' % (av.snclId))
                    else:
                        logger.warning('No data available for %s from %s: %s' % (av.snclId, concierge.dataselect_url, e))
                    continue
                
                if len(utils.get_slot(r_stream, 'traces')) > 1 :
                    logger.info('Skipping %s because it has gaps' % (av.snclId))
                else:
                    streamList.append(r_stream)
                    
            if len(streamList) == 0:
                logger.info('Skipping %s because it has no usable channels' % (sn_lId))
                continue
                
            if len(streamList) == 1:
                logger.info('Skipping %s because it only has usable data for one channel' % (sn_lId))
                continue   

            # Run the correlation metrics -----------------------

            # At this point, each stream in streamList has only one trace
            # and can now be used in the correlation metric.
            
            logger.debug('Calculating crossTalk metrics for %d streams' % (len(streamList)))

            # 1-2
            l0 = utils.get_slot(streamList[0],'npts')
            c0 = utils.get_slot(streamList[0],'channel')
            l1 = utils.get_slot(streamList[1],'npts')
            c1 = utils.get_slot(streamList[1],'channel')
            
            if len(streamList) == 2:
                if( abs(l0 - l1) > 2):
                    logger.info('Skipping %s because the number of data samples differs between channels. Incompatible lengths %s=%d, %s=%d' % (sn_lId,c0,l0,c1,l1))
                    continue
                try:
                    df = irismustangmetrics.apply_correlation_metric(streamList[0], streamList[1], 'correlation')
                    dataframes.append(df)
                except Exception as e:
                    logger.warning('"crossTalk" metric calculation failed for %s: %s' % (av.snclId, e))
            
            if len(streamList) == 3:
                l2 = utils.get_slot(streamList[2],'npts')
                c2 = utils.get_slot(streamList[2],'channel')

                if( abs(l0 - l1) > 2 and abs(l1-l2) > 2 and abs(l0-l2) > 2):
                    logger.info('Skipping %s because the number of data samples differs between channels. Incompatible lengths %s=%d, %s=%d, %s=%d' % (sn_lId,c0,l0,c1,l1,c2,l2))
                    continue

                # 1-2
                if( abs(l0 - l1) <= 2):
                    try:
                        df = irismustangmetrics.apply_correlation_metric(streamList[0], streamList[1], 'correlation')
                        dataframes.append(df)
                    except Exception as e:
                        logger.warning('"crossTalk" metric calculation failed for %s: %s' % (av.snclId, e))
                else:
                    logger.info('Skipping %s %s:%s because the number of data samples differs between channels. Incompatible lengths %s=%d, %s=%d' % (sn_lId,c0,c1,c0,l0,c1,l1))

                # 1-3
                if( abs(l0 - l2) <= 2):
                    try:
                        df = irismustangmetrics.apply_correlation_metric(streamList[0], streamList[2], 'correlation')
                        dataframes.append(df)
                    except Exception as e:
                        logger.warning('"crossTalk" metric calculation failed for %s: %s' % (av.snclId, e))
                else:
                    logger.info('Skipping %s %s:%s because the number of data samples differs between channels. Incompatible lengths %s=%d, %s=%d' % (sn_lId,c0,c2,c0,l0,c2,l2))
                
                # 2-3
                if( abs(l1 - l2) <= 2):
                    try:
                        df = irismustangmetrics.apply_correlation_metric(streamList[1], streamList[2], 'correlation')
                        dataframes.append(df)
                    except Exception as e:
                        logger.warning('"crossTalk" metric calculation failed for %s: %s' % (av.snclId, e))
                else:
                    logger.info('Skipping %s %s:%s because the number of data samples differs between channels. Incompatible lengths %s=%d, %s=%d' % (sn_lId,c1,c2,c1,l1,c2,l2))
                    

        # End of sn.lId loop

    # End of event loop

    # Concatenate and filter dataframes before returning -----------------------
    
    # Create a boolean mask for filtering the dataframe
    def valid_metric(x):
        return x in concierge.metric_names
        
    if len(dataframes) == 0:
        logger.warning('"cross_talk" metric calculation generated zero metrics')
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
