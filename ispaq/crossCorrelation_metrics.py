"""
ISPAQ Business Logic for Cross-Correlation Metrics.

:copyright:
    Mazama Science
:license:
    GNU Lesser General Public License, Version 3
    (http://www.gnu.org/copyleft/lesser.html)
"""
from obspy import UTCDateTime
from obspy.clients.fdsn import Client

import math
import numpy as np
import pandas as pd

import utils
import irisseismic
import irismustangmetrics


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

        logger.debug('%03d Magnitude %3.1f event: %s' % (index, event.magnitude, event.eventLocationName))
        
        # Sanity check
        if pd.isnull(event.latitude) or pd.isnull(event.longitude):
            logger.debug('skipping event because of missing longitude or latitude')
            continue
    
        # Sanity check
        if pd.isnull(event.depth):
            logger.debug('skipping event because of missing depth')
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
            logger.error('skipping event because get_availability failed: %s' % (e))
            continue
                    
        # Sanity check that some SNCLs exist
        if availability.shape[0] == 0:
            logger.debug('skipping event because no SNCLs are available')
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
                logger.error('skipping because getTravelTime failed: %s' % (e))
                continue
             
            windowStart = event.time + min(tt.travelTime) - windowSecs/2.0
            windowEnd = event.time + min(tt.travelTime) + windowSecs/2.0

            try:
                r_stream1 = concierge.get_dataselect(av1.network, av1.station, av1.location, av1.channel, windowStart, windowEnd)
            except Exception as e:
                logger.warning('unable to obtain data for %s from %s: %s' % (av1.snclId, concierge.dataselect_url, e))
                continue
            
            # No metric calculation possible if SNCL has more than one trace
            if len(utils.get_slot(r_stream1, 'traces')) > 1 :
                logger.debug('skipping %s because it has more than one trace' % (av.snclId))
                continue

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
                logger.error('skipping SNCL because get_availability failed: %s' % (e))
                continue

            # Sanity check that some SNCLs exist
            if availability2.shape[0] == 0:
                logger.debug('skipping SNCL because no nearby SNCLs are available')
                continue

            logger.debug('Found %d nearby SNCLs' % (availability2.shape[0]))

            # Create masks to find any other SNCLs against which we want to cross-correlate

            # Not this station
            stationMask = availability2.station != av1.station

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
            mask = stationMask & channelMask

            if not any(mask):
                logger.debug('skipping SNCL because no nearby SNCLs are compatible')
                continue
            else:
                avCompatible = availability2[mask]
                # To find the closest SNCL -- order rows by distance and take the first row
                ###avCompatible['dist'] = irisseismic.surfaceDistance(av1.latitude, av1.longitude, avCompatible.latitude, avCompatible.longitude)
                ###avCompatible = avCompatible.sort('dist', ascending=False)
                #avCompatible <- avCompatible[order(avCompatible$dist),]
                
                debug_point = 1

            # ----- Compatible SNCLs found.  Find the closest one with data ------------

            #for (index2 in seq(nrow(avCompatible))) {

                #av2 <- avCompatible[index2,]

                ## Get data in a window centered on the event's arrival at station #2
                #result <- try( tt <- IRISSeismic::getTraveltime(iris, event$latitude, event$longitude, event$depth, av2$latitude, av2$longitude),
                               #silent=TRUE )

                #profilePoint("getTraveltime","seconds to get traveltime data")

                ## Skip to the next SNCL if any error was encountered
                #if ( class(result)[1] == "try-error" ) {
                    #setProcessExitCode( MCRErrorMessage(geterrmessage(), "TRAVELTIME", av2$snclId) )
                    #next
                #}

                #windowStart <- event$time + min(tt$travelTime) - windowSecs/2
                #windowEnd <- event$time + min(tt$travelTime) + windowSecs/2

                #result <- try( st2 <- IRISSeismic::getDataselect(iris,av2$network,av2$station,av2$location,av2$channel,windowStart,windowEnd),
                               #silent=TRUE )

                #profilePoint("getDataselect","seconds to get waveform data")

                #if (class(result)[1] == "try-error" ) {      
                    #setProcessExitCode( MCRErrorMessage(geterrmessage(), "DATASELECT", av2$snclId) )
                    #next
                    #} else {
                        ## Found everything we need, so end the loop
                #break
                #}

            #}

            ## ----- Second SNCL found.  Now on to calculate cross-correlation ----------

            ## Choose low-pass filtering
            #filter <- signal::butter(defaultFilterArgs[1],defaultFilterArgs[2])

            ## Calculate the cross-correlation metrics and append them to the list
            #result <- try( tempList <- IRISMustangMetrics::crossCorrelationMetric(st1, st2, maxLagSecs, filter),
                           #silent=TRUE )

            #profilePoint("metricCalculation","seconds to calculate crossCorrelationMetric")

            #if (class(result)[1] == "try-error" ) {
                #setProcessExitCode( MCRWarning(geterrmessage()) )
                #next
                #} else {
                    #metricList <- append(metricList,tempList)
                #}

        #} # END of SNCL loop

    #} # END of event loop



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
