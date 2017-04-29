"""
ISPAQ Business Logic for Cross-Correlation Metrics.

:copyright:
    Mazama Science
:license:
    GNU Lesser General Public License, Version 3
    (http://www.gnu.org/copyleft/lesser.html)
"""
# output is polarity_check metric

from __future__ import (absolute_import, division, print_function)

import math
import numpy as np
import pandas as pd
import obspy

from obspy import UTCDateTime
from obspy import geodetics
from obspy import taup
from obspy.taup import TauPyModel
model = TauPyModel(model="iasp91")

from .concierge import NoAvailableDataError

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
        
    # Default parameters from IRISMustangUtils::generateMetrics_crossCorrelation or crossCorrelationMetrics_exec.R
    channelFilter = "[CBFHLM][HX]."    
    minmag = 6.5
    eventMinradius = 15
    eventMaxradius = 90
    snclMinradius = 0
    snclMaxradius = 15
    windowSecs = 600
    maxLagSecs = 10
        
    # Sanity check for metadata
    if concierge.station_url is None:
        logger.warning('No station metadata found for crossCorrelation metrics')
        return None

    # Get the seismic events in this time period
    events = concierge.get_event(minmag=minmag)
        
    # Sanity check
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

        logger.debug("Looking for metadata from %s to %s" % (halfHourStart,halfHourEnd))
        try:        
            availability = concierge.get_availability(starttime=halfHourStart, endtime=halfHourEnd,
                                                      longitude=event.longitude, latitude=event.latitude,
                                                      minradius=eventMinradius, maxradius=eventMaxradius)
        except NoAvailableDataError as e:
            logger.info('Skipping event with no available data')
            continue
        except Exception as e:
            logger.warning('Skipping event %s %s  because concierge.get_availability failed: %s' % (event.magnitude, event.eventLocationName, e))
            continue
        if availability is None:
            logger.info("Skipping event with no available data")
            continue            

        # Apply the channelFilter
        availability = availability[availability.channel.str.contains(channelFilter)]      

    
        # ----- All available SNCLs -------------------------------------------------

        # function metadata dictionary
        function_metadata = concierge.function_by_logic['crossCorrelation']
    
        # Loop over rows of the availability dataframe
        for (index, av1) in availability.iterrows():

            if math.isnan(av1.latitude) or math.isnan(av1.longitude):
                logger.info("No metadata for " + av1.snclId + ": skipping")
                continue 

            snclId = av1.snclId
            
            logger.debug('Working on %s' % (snclId))

            # Get data in a window centered on the event's arrival at station #1
             
            dist = obspy.geodetics.base.locations2degrees(event.latitude, event.longitude, av1.latitude, av1.longitude)
            arrivals = model.get_travel_times(source_depth_in_km=event.depth,distance_in_degree=dist)

            tt=min(arrivals,key=lambda x: x.time).time

            windowStart = event.time + tt - windowSecs/2.0
            windowEnd = event.time + tt + windowSecs/2.0

            logger.debug("Looking for data for %s from %s to %s" % (av1.snclId, windowStart, windowEnd))

            try:
                r_stream1 = concierge.get_dataselect(av1.network, av1.station, av1.location, av1.channel, windowStart, windowEnd)
            except Exception as e:
                if str(e).lower().find('no data') > -1:
                    logger.info('No data available for %s' % (av1.snclId))
                else:
                    logger.warning('No data available for %s from %s: %s' % (av1.snclId, concierge.dataselect_url, e))
                continue
            
            # No metric calculation possible if SNCL has more than one trace 
            if len(utils.get_slot(r_stream1, 'traces')) > 1 :
                logger.info('Skipping %s because it has gaps' % (av1.snclId))
                continue

            # If metadata indicates reversed polarity (dip>0), invert the amplitudes (met 2016/03/03)
            if av1.channel[2] == 'Z' and av1.dip > 0:
                r_stream1 = irisseismic.multiplyBy(r_stream1, -1.0)


            # ----- Now query again to find ANY SNCL near the SNCL of interest ---------

            # Create the regex for channel matching - must be same channel type
	    sncl1ch1 = snclId.split('.')[-1][0]
	    sncl1ch2 = snclId.split('.')[-1][1]
            channelString = "%s%s?" % (sncl1ch1,sncl1ch2)

            logger.debug("Looking for metadata for %s to %s within radius %s-%s degrees" % (halfHourStart, halfHourEnd, snclMinradius, snclMaxradius))

            # Get the data availability using spatial search parameters
            try:
                availability2 = concierge.get_availability(network='*', station='*', location='*', channel=channelString,
                                                           starttime=halfHourStart, endtime=halfHourEnd,
                                                           longitude=av1.longitude, latitude=av1.latitude,
                                                           minradius=snclMinradius, maxradius=snclMaxradius)
            except Exception as e:
                logger.warning('Skipping %s because get_availability failed for nearby stations: %s' % (av1.snclId, e))
                continue
            if availability2 is None:
                logger.info("Skipping %s with no available stations" % (av1.snclId))
                continue

            # Sanity check that some SNCLs exist
            if availability2.shape[0] == 0:
                logger.info('Skipping %s with no available stations' % (av1.snclId))
                continue

            # Not this station
            stationMask = availability2.station != av1.station
            availability2 = availability2[stationMask]

            logger.debug('Found %d nearby SNCLs' % (availability2.shape[0]))

            # Create masks to find any other SNCLs against which we want to cross-correlate

            # We only want to include those sncls that have sample rate information
            metaMask = availability2.samplerate.isnull().values
            metaMask = metaMask == False
            availability2 = availability2[metaMask]

            # Sample rate compatibility, sample rates must be  multiples of each other  (assumes sample rate >= 1, pracma::rem requires integer values)
            # FutureWarning: in the future, np.full(3, 40) will return an array of dtype('int64')

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
            mask = channelMask & sampleRateMask

            if not any(mask):
                logger.info('Skipping %s with no compatible stations' % (av1.snclId))
                continue
            else:
                avCompatible = availability2[mask].reset_index()
                # To find the closest SNCL -- order rows by distance and take the first row
                avCompatible['dist'] = pd.Series(irisseismic.surfaceDistance(av1.latitude, av1.longitude, avCompatible.latitude, avCompatible.longitude))
                avCompatible = avCompatible.sort_values('dist', ascending=True)
                
            # ----- Compatible SNCLs found.  Find the closest one with data ------------

            for (index2, av2) in avCompatible.iterrows():
                if math.isnan(av2.latitude) or math.isnan(av2.longitude):
                    logger.debug("No metadata for " + av2.snclId + ": skipping")
                    continue
                
                lastsncl = avCompatible.snclId[-1:].to_string(index=False)
                testx = 0

                # Get data in a window centered on the event's arrival at station #2
                try:
                    tt = irisseismic.getTraveltime(event.latitude, event.longitude, event.depth, 
                                                   av2.latitude, av2.longitude)
                except Exception as e:
                    logger.warning('Skipping %s:%s because getTravelTime failed: %s' % (av1.snclId, av2.snclId, e))
                    if av2.snclId is lastsncl:
                        testx = 1
                    continue                  
                
                windowStart = event.time + min(tt.travelTime) - windowSecs/2.0
                windowEnd = event.time + min(tt.travelTime) + windowSecs/2.0

                logger.debug("Looking for near neighbor station %s from %s to %s" % (av2.snclId, windowStart, windowEnd))

                try:
                    r_stream2 = concierge.get_dataselect(av2.network, av2.station, av2.location, av2.channel, windowStart, windowEnd)
                except Exception as e:
                    if str(e).lower().find('no data') > -1:
                        logger.debug('No data available for %s' % (av2.snclId))
                    else:
                        logger.warning('No data available for %s from %s: %s' % (av2.snclId, concierge.dataselect_url, e))
                    if av2.snclId is lastsncl:
                        testx = 1
                    continue
                   
                # Check for actual sample rate compatibility
                sampler1 = utils.get_slot(r_stream1,'sampling_rate')
                sampler2 = utils.get_slot(r_stream2,'sampling_rate')
     
                if sampler1 >= 1 and sampler2 >= 1: 
                    sr1 = int(round(sampler1,1))
                    sr2 = int(round(sampler2,1))
                    if (sr1 % sr2 != 0 ) and (sr2 % sr1 != 0): 
                        logger.debug('Skipping %s:%s because actual sample rates are not compatible, %s:%s' % (av1.snclId, av2.snclId, sr1, sr2))
                        if av2.snclId == lastsncl:
                            testx = 1
                        continue

            
                # NOTE:  This check is missing from IRISMustangUtils/R/generateMetrics_crossCorrelation.R
                # No metric calculation possible if SNCL has more than one trace
                if len(utils.get_slot(r_stream2, 'traces')) > 1:
                    logger.debug('Skipping %s because it has gaps' % (av2.snclId))
                    if av2.snclId is lastsncl:
                        testx = 1
                    continue

                else:
                    # Found everything we need so end the loop
                    break

            # ----- Second SNCL found.  Now on to calculate cross-correlation ----------
 
            # if last avCompatible snclid doesn't pass checks it will end up here. 
            if testx == 1:
                logger.info('Skipping %s because no compatible stations found' % (av1.snclId))
                continue

            # Calculate the cross-correlation metrics and append them to the list
            logger.info('Calculating crossCorrelation metrics for %s:%s' % (av1.snclId, av2.snclId))
            try:
                df = irismustangmetrics.apply_correlation_metric(r_stream1, r_stream2, 'crossCorrelation', maxLagSecs)
                dataframes.append(df)
            except Exception as e:
                logger.warning('"crossCorrelation" metric calculation failed for %s:%s: %s' % (av1.snclId, av2.snclId, e))

        # END of SNCL loop

    # END of event loop



    # Concatenate and filter dataframes before returning -----------------------
    
    # Create a boolean mask for filtering the dataframe
    def valid_metric(x):
        return x in concierge.metric_names
        
    if len(dataframes) == 0:
        logger.warning('"cross_correlation" metric calculation generated zero metrics')
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
