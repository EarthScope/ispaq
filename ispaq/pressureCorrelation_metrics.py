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


def pressureCorrelation_metrics(concierge):
    """
    Generate *pressureCorrelation* metrics.

    :type concierge: :class:`~ispaq.concierge.Concierge`
    :param concierge: Data access expiditer.
    
    :rtype: pandas dataframe (TODO: change this)
    :return: Dataframe of pressureCorrelation metrics. (TODO: change this)

    .. rubric:: Example

    TODO:  doctest examples
    """
    # Get the logger from the concierge
    logger = concierge.logger
    
    # Container for all of the metrics dataframes generated
    dataframes = []

    # Default parameters from IRISMustangUtils::generateMetrics_crossTalk
    includleRestricted = False
    channelFilter = "LH."
    pressureLocation = "*"
    pressureChannel = "LDO"

    # ----- All available SNCLs -------------------------------------------------
    # Loop over days
    start = concierge.requested_starttime
    end = concierge.requested_endtime
    nday = int(end.julday - start.julday) + 1 
    for day in range(nday):
        starttime = (start + day * 86400)
        starttime = UTCDateTime(starttime.strftime("%Y-%m-%d") +"T00:00:00Z")
        endtime = starttime + 86400

        if starttime == end:
            continue
        if starttime <= start:
            starttime = start
        if endtime >= end:
            endtime = end

        try:
            pressureAvailability = concierge.get_availability(location=pressureLocation, channel=pressureChannel,starttime=starttime,endtime=endtime)
        except Exception as e:
            logger.error('Metric calculation failed because concierge.get_availability failed: %s' % (e))
            return None
    
        if pressureAvailability is None or pressureAvailability.shape[0] == 0:
            logger.info('No pressure channels available')
            continue
        else:
            logger.info('%d pressure channels available' % (pressureAvailability.shape[0]))
   
 
        # Loop over rows of the availability dataframe
        for (pIndex, pAv) in pressureAvailability.iterrows():
        
            logger.info(' %03d Pressure channel %s' % (pIndex, pAv.snclId))
        
            # Get the data ----------------------------------------------

            try:
                r_pStream = concierge.get_dataselect(pAv.network, pAv.station, pAv.location, pAv.channel, starttime, endtime, inclusiveEnd=False)
            except Exception as e:
                if str(e).lower().find('no data') > -1:
                    logger.warning('No data for %s' % (pAv.snclId))
                else:
                    logger.warning('No data for %s from %s: %s' % (pAv.snclId, concierge.dataselect_url, e))
                continue

            # Merge traces -- gracefully go to next in loop if an error reported
            try:
                r_pStream = irisseismic.mergeTraces(r_pStream)
            except Exception as e:
                logger.debug("%s" % (e))
                continue

            # Get all desired seismic channels for this network-station
            seismicAvailability = concierge.get_availability(pAv.network, pAv.station)
        
            # Apply the channelFilter
            seismicAvailability = seismicAvailability[seismicAvailability.channel.str.contains(channelFilter)]
            if seismicAvailability is None or seismicAvailability.shape[0] == 0:
                logger.debug('No seismic %s channels available' % (channelFilter))
                continue
                
            # Find the locations associated with seismic channels
            locations = list(seismicAvailability.location.unique())
    
            # NOTE:  At each unique location we should have a triplet of seismic channels that can
            # NOTE:  be correlated with the pressure channel
            ############################################################
            # Loop through all locations with seismic data that can be
            # correlated to this pressure channel.
            ############################################################

            for loc in locations:
    
                logger.debug('Working on location %s' % (loc))
            
                locationAvailability = seismicAvailability[seismicAvailability.location == loc]
    
                if locationAvailability is None or locationAvailability.shape[0] == 0:
                    logger.debug('No location %s channels available' %s (loc))
                    continue
         
                ############################################################
                # Loop through all seismic channels at this SN.L
                ############################################################
            
                # Loop over rows of the availability dataframe
                for (index, lAv) in locationAvailability.iterrows():
                    try:
                        r_stream = concierge.get_dataselect(lAv.network, lAv.station, lAv.location, lAv.channel, starttime, endtime,inclusiveEnd=False)
                    except Exception as e:
                        if str(e).lower().find('no data') > -1:
                            logger.debug('No data for %s' % (lAv.snclId))
                        else:
                            logger.warning('No data for %s from %s: %s' % (lAv.snclId, concierge.dataselect_url, e))
                        continue
                
                    # Merge traces -- gracefully go to next in loop if an error reported
                    try:
                        r_stream = irisseismic.mergeTraces(r_stream)
                    except Exception as e:
                        logger.debug("%s" % (e))
                        continue
                
                    logger.debug('Calculating pressureCorrelation metrics for %s:%s on %s' % (pAv.snclId, lAv.snclId,starttime.date))
                    try:
                        df = irismustangmetrics.apply_correlation_metric(r_pStream, r_stream, 'correlation')
                        dataframes.append(df)
                    except Exception as e:
                        logger.warning('"pressure_effects" metric calculation failed for %s:%s: %s' % (pAv.snclId, lAv.snclId, e))              
                # End of locationAvailability loop
    
            # End of locations loop
    
        # End of pressureAvailability loop	

    # End of day loop

    # Concatenate and filter dataframes before returning -----------------------

    if len(dataframes) == 0:
        logger.warn('"pressure_correlation" metric calculation generated zero metrics')
        return None
    else:
        result = pd.concat(dataframes, ignore_index=True) 
        # Change metricName to "pressure_effects"
        result['metricName'] = 'pressure_effects'
        result.reset_index(drop=True, inplace=True)        
        return(result)


# ------------------------------------------------------------------------------


if __name__ == '__main__':
    import doctest
    doctest.testmod(exclude_empty=True)
