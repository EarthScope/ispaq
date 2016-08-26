"""
ISPAQ Business Logic for Cross-Correlation Metrics.

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


def crossCorrelation_metrics(concierge):
    """
    Generate *crossCorrelation* metrics.

    :type concierge: :class:`~ispaq.concierge.Concierge`
    :param concierge: Data access expiditer.
    
    :rtype: pandas dataframe
    :return: Dataframe of simple metrics.

    .. rubric:: Example

    TODO:  doctest examples
    """
    # Get the logger from the concierge
    logger = concierge.logger
        
    # Default parameters from IRISMustangUtils::generateMetrics_crossCorrelation
    minmag = 6.5
    eventMinradius = 15
    eventMaxradius = 90
    snclMinradius = 0
    snclMaxradius = 15
    windowSecs = 600
    maxLagSecs = 10
    ch1 = ['B','H']
    ch2 = ['H']
    defaultFilterArgs = [2,0.01]    
        
    # Get the seismic events in this time period
    events = concierge.get_event(minmag=minmag)
        
    # Sanity checck
    if events is None or events.shape[0] == 0:
        logger.info('No events found for crossCorrelation metrics.')
        return None
        
    # Container for all of the metrics dataframes generated
    dataframes = []

    #############################################################
    ## Loop through each event.
    #############################################################

    logger.info('Calculating crossCorrelation metrics for %d events' % events.shape[0])

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
                                                      minradius=eventMinradius, maxradius=eventMaxradius)
        except Exception as e:
            logger.debug('Skipping event because get_availability failed: %s' % (e))
            continue
                    
        # Sanity check that some SNCLs exist
        if availability.shape[0] == 0:
            logger.debug('Skipping event because no SNCLs are available')
            continue
    
        # ----- All available SNCLs -------------------------------------------------

        # function metadata dictionary
        function_metadata = concierge.function_by_logic['crossCorrelation']
    
        # Loop over rows of the availability dataframe
        for (index, av1) in availability.iterrows():
            
            snclId = av1.snclId
            
            logger.debug('Working on %s' % (snclId))

            # Get data in a window centered on the event's arrival at station #1
            try:
                tt = irisseismic.getTraveltime(event.latitude, event.longitude, event.depth, 
                                               av1.latitude, av1.longitude)
            except Exception as e:
                logger.debug('Skipping because getTravelTime failed: %s' % (e))
                continue
             
            windowStart = event.time + min(tt.travelTime) - windowSecs/2.0
            windowEnd = event.time + min(tt.travelTime) + windowSecs/2.0

            try:
                r_stream1 = concierge.get_dataselect(av1.network, av1.station, av1.location, av1.channel, windowStart, windowEnd)
            except Exception as e:
                if str(e).lower().find('no data') > -1:
                    logger.debug('No data for %s' % (av1.snclId))
                else:
                    logger.debug('No data for %s from %s: %s' % (av1.snclId, concierge.dataselect_url, e))
                continue
            
            # No metric calculation possible if SNCL has more than one trace
            if len(utils.get_slot(r_stream1, 'traces')) > 1 :
                logger.debug('Skipping %s because it has more than one trace' % (av.snclId))
                continue

            # If metadata indicates reversed polarity (dip>0), invert the amplitudes (met 2016/03/03)
            if av1.channel[2] == 'Z' and av1.dip > 0:
                r_stream1 = irisseismic.multiplyBy(r_stream1, -1.0)


            # ----- Now query again to find ANY SNCL near the SNCL of interest ---------

            # Create the regex for all appropriate channels to match for channel 2
            channels = pd.Series(ch1*len(ch2)) + pd.Series(ch2*len(ch1)) + '?'
            channelString = ','.join(channels)
            
            logger.debug('Calling get_availability for all SNCLs that match "%s"' % (channelString))

            # Get the data availability using spatial search parameters
            try:        
                availability2 = concierge.get_availability(network='*', station='*', location='*', channel=channelString,
                                                           starttime=halfHourStart, endtime=halfHourEnd,
                                                           longitude=av1.longitude, latitude=av1.latitude,
                                                           minradius=snclMinradius, maxradius=snclMaxradius)
            except Exception as e:
                logger.debug('Skipping SNCL because get_availability failed: %s' % (e))
                continue

            # Sanity check that some SNCLs exist
            if availability2.shape[0] == 0:
                logger.debug('Skipping SNCL because no nearby SNCLs are available')
                continue

            logger.debug('Found %d nearby SNCLs' % (availability2.shape[0]))

            # Create masks to find any other SNCLs against which we want to cross-correlate

            # Not this station
            stationMask = availability2.station != av1.station

            # Sample rate compatibility, sample rates must be  multiples of each other  (assumes sample rate >= 1, pracma::rem requires integer values)
            a = availability2.samplerate.apply(lambda x: int(x))
            b = pd.Series(np.full(len(a),int(av1.samplerate)))
            sampleRateMask = (a >= np.ones(len(a))) & ( (a % b == 0) | (b % a == 0) )

            # Channel compatibility
            if av1.channel[2] == 'Z':
                # For Z channels, any matching channel is compatible
                channelMask = availability2.channel == av1.channel
            else:
                # For horizontal channels, find all non-Z channel with an azimuth within 5 degrees of av1
                ch = av1.channel[0:2]
                chMask = availability2.channel.str.contains(ch)
                nonZMask = -availability2.channel.str.contains('Z')
                azimuthAngle = abs(av1.azimuth - availability2.azimuth) * math.pi/180.0
                maxAzimuthAngle = 5.0 * math.pi/180.0
                azimuthMask = azimuthAngle.apply(math.cos) >= math.cos(maxAzimuthAngle)
                channelMask = chMask & nonZMask & azimuthMask
                
            # Bitwise AND to get the final mask
            mask = stationMask & channelMask & sampleRateMask

            if not any(mask):
                logger.debug('Skipping SNCL because no nearby SNCLs are compatible')
                continue
            else:
                avCompatible = availability2[mask].reset_index()
                # To find the closest SNCL -- order rows by distance and take the first row
                avCompatible['dist'] = pd.Series(irisseismic.surfaceDistance(av1.latitude, av1.longitude, avCompatible.latitude, avCompatible.longitude))
                avCompatible = avCompatible.sort_values('dist', ascending=True)
                
            # ----- Compatible SNCLs found.  Find the closest one with data ------------

            #for (index2 in seq(nrow(avCompatible))) {
            for (index2, av2) in avCompatible.iterrows():
                
                debug_point = 1

                # Get data in a window centered on the event's arrival at station #2
                try:
                    tt = irisseismic.getTraveltime(event.latitude, event.longitude, event.depth, 
                                                   av2.latitude, av2.longitude)
                except Exception as e:
                    logger.debug('Skipping because getTravelTime failed: %s' % (e))
                    continue
                
                windowStart = event.time + min(tt.travelTime) - windowSecs/2.0
                windowEnd = event.time + min(tt.travelTime) + windowSecs/2.0

                try:
                    r_stream2 = concierge.get_dataselect(av2.network, av2.station, av2.location, av2.channel, windowStart, windowEnd)
                except Exception as e:
                    if str(e).lower().find('no data') > -1:
                        logger.debug('No data for %s' % (av2.snclId))
                    else:
                        logger.debug('No data for %s from %s: %s' % (av2.snclId, concierge.dataselect_url, e))
                    continue
                
                # NOTE:  This check is missing from IRISMustangUtils/R/generateMetrics_crossCorrelation.R
                # No metric calculation possible if SNCL has more than one trace
                if len(utils.get_slot(r_stream2, 'traces')) > 1 :
                    logger.debug('Skipping %s because it has more than one trace' % (av2.snclId))
                    continue
                else:
                    # Found everything we need so end the loop
                    break

            # ----- Second SNCL found.  Now on to calculate cross-correlation ----------

            # Choose low-pass filtering
            r_filter = irisseismic.butter(defaultFilterArgs[0],defaultFilterArgs[1])

            # Calculate the cross-correlation metrics and append them to the list
            logger.debug('Calculating crossCorrelation metrics for %s:%s' % (av1.snclId, av2.snclId))
            try:
                df = irismustangmetrics.apply_correlation_metric(r_stream1, r_stream2, 'crossCorrelation', maxLagSecs, r_filter)
                dataframes.append(df)
            except Exception as e:
                logger.debug('"crossCorrelation" metric calculation failed for %s:%s: %s' % (av1.snclId, av2.snclId, e))
            

        # END of SNCL loop

    # END of event loop



    # Concatenate and filter dataframes before returning -----------------------
    
    # Create a boolean mask for filtering the dataframe
    def valid_metric(x):
        return x in concierge.metric_names
        
    if len(dataframes) == 0:
        logger.warn('"cross_correlation" metric calculation generated zero metrics')
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
