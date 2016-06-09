"""
ISPAQ Business Logic for Orientation Check Metrics.

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
from obspy.clients.fdsn import Client

from . import utils
from . import irisseismic
from . import irismustangmetrics


def orientationCheck_metrics(concierge):
    """
    Generate *orientationCheck* metrics.

    :type concierge: :class:`~ispaq.concierge.Concierge`
    :param concierge: Data access expiditer.
    
    :rtype: pandas dataframe
    :return: Dataframe of simple metrics.

    .. rubric:: Example

    TODO:  doctest examples
    """
    # Get the logger from the concierge
    logger = concierge.logger
        
    # Default parameters from IRISMustangUtils::generateMetrics_orientationCheck
    minmag = 6.0 # TODO:  Change back to 7.0 to match R code
    maxdepth = 100
    eventMinradius = 0
    eventMaxradius = 180
    windowSecsBefore = 20
    windowSecsAfter = 600
    taper = 0.05
    filterArgs = [2,0.02,0.04]    
    degreeIncrement = 1
        
    # Get the seismic events in this time period
    events = concierge.get_event(minmag=minmag)
        
    # Sanity checck
    if events is None or events.shape[0] == 0:
        logger.info('No events found for orientationCheck metrics.')
        return None
        
    # Container for all of the metrics dataframes generated
    dataframes = []

    #############################################################
    ## Loop through each event.
    #############################################################

    logger.info('Calculating orientationCheck metrics for %d events' % events.shape[0])

    for (index, event) in events.iterrows():

        logger.debug('%03d Magnitude %3.1f event: %s' % (index, event.magnitude, event.eventLocationName))
        
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
            logger.debug('skipping event because get_availability failed: %s' % (e))
            continue
                    
        # Sanity check that some SNCLs exist
        if availability.shape[0] == 0:
            logger.debug('Skipping event because no SNCLs are available')
            continue
    
        ############################################################
        # Loop through the SN.L combinations
        ############################################################
    
        # Channel types (as opposed to orientation) will contain only the first two characters
        channelType = availability.channel.apply(lambda x: x[0:2])
    
        # Find unique network-station-location combinations
        sn_lIds = availability.network + '.' + availability.station + '.' + availability.location + '.' + channelType
    
        # Add sn_lId to the availability dataframe for easy detection
        availability['sn_lId'] = sn_lIds

        # ----- All available SNCLs -------------------------------------------------

        for sn_lId in sorted(list(set(sn_lIds))):

            logger.debug('Working on SN.L %s' % (sn_lId))

            sn_lAvailability = availability[availability.sn_lId == sn_lId]
            
            if sn_lAvailability.shape[0] != 3:
                logger.debug('Skipping %s because there is only %d channels were found at this SN.L' % (sn_lId, sn_lAvailability.shape[0]))
                continue

            # Determine N, E and Z channels
            N_or_1_mask = sn_lAvailability.channel.str.contains('..N') | sn_lAvailability.channel.str.contains('..1')
            E_or_2_mask = sn_lAvailability.channel.str.contains('..E') | sn_lAvailability.channel.str.contains('..2')
            Z_mask = sn_lAvailability.channel.str.contains('..Z')
            Channel_1 = sn_lAvailability[N_or_1_mask].iloc[0]
            Channel_2 = sn_lAvailability[E_or_2_mask].iloc[0]
            ZChannel = sn_lAvailability[Z_mask].iloc[0]
    
            # Calculate various distances and surface travel time
            distaz = irisseismic.getDistaz(event.latitude,event.longitude,ZChannel.latitude,ZChannel.longitude)
    
            surfaceDistance = irisseismic.surfaceDistance(event.latitude,event.longitude,ZChannel.latitude,ZChannel.longitude)[0]
            surfaceTravelTime = surfaceDistance / 4.0 # km  / (km/sec)


            # Get the data -----------------------------------------
        
            #         request 3-channel instrument-corrected (or scaled) data for one station/loc/sample_rate
            #             starting 20s before the predicted Rayleigh wave and ending 600s after.
            #         Apply a 10% cosine taper to each channel
            #         Bandpass filter from 0.02 to 0.04 Hz (50-25s)
            #         Take the Hilbert transform of the Z channel
        
            windowStart = event.time + surfaceTravelTime - windowSecsBefore
            windowEnd = event.time + surfaceTravelTime + windowSecsAfter
        
            try:
                stN = concierge.get_dataselect(Channel_1.network, Channel_1.station, Channel_1.location,Channel_1.channel,
                                                    windowStart, windowEnd, inclusiveEnd=False)
            except Exception as e:
                if str(e).lower().find('no data') > -1:
                    logger.debug('No data for %s' % (Channel_1.snclId))
                else:
                    logger.debug('No data for %s from %s: %s' % (Channel_1.snclId, concierge.dataselect_url, e))
                continue
        
            try:
                stE = concierge.get_dataselect(Channel_2.network, Channel_2.station, Channel_2.location,Channel_2.channel,
                                                    windowStart, windowEnd, inclusiveEnd=False)
            except Exception as e:
                if str(e).lower().find('no data') > -1:
                    logger.debug('No data for %s' % (Channel_2.snclId))
                else:
                    logger.debug('No data for %s from %s: %s' % (Channel_2.snclId, concierge.dataselect_url, e))
                continue
        
            try:
                stZ = concierge.get_dataselect(ZChannel.network, ZChannel.station, ZChannel.location,ZChannel.channel,
                                                    windowStart, windowEnd, inclusiveEnd=False)
            except Exception as e:
                if str(e).lower().find('no data') > -1:
                    logger.debug('No data for %s' % (ZChannel.snclId))
                else:
                    logger.debug('No data for %s from %s: %s' % (ZChannel.snclId, concierge.dataselect_url, e))
                continue
        
        
            # If metadata indicates reversed polarity (dip>0), invert the amplitudes (met 2016/03/07)
            if (ZChannel.dip > 0):
                stZ = irisseismic.multiplyBy(stZ,-1)
        
            if len(utils.get_slot(stN,'traces')) > 1 or len(utils.get_slot(stE,'traces')) > 1 or len(utils.get_slot(stZ,'traces')) > 1:
                logger.debug('Skipping %s becuase it has gaps' % (sn_lId)) 
                continue
        
            # complain if sample lengths differ by more than 1 sample
            l1 = utils.get_slot(stN,'npts')
            l2 = utils.get_slot(stE,'npts')
            l3 = utils.get_slot(stZ,'npts')
      
            if( abs(l1 - l2) > 1  or abs(l1 - l3) > 1 ):
                logger.debug('Incompatible lengths stN=%d, stE=%d, stZ=%d' % (l1,l2,l3))
                continue
            else:
                max_length = min(l1, l2, l3)
                
                
            # NOTE:  This next function captures a chunk of functionality that involves direct
            # NOTE:  manipulation of individual slots in Stream objects.
            # NOTE:  This requires some R knowledge and rpy2 trickery that doesn't belong in 
            # NOTE:  the business logic python code.
 
            (stN, stE, stZ, HZ) = irisseismic.trim_taper_filter(stN, stE, stZ, max_length, taper, filterArgs)
            
            
            #         For trial empirical BHN/BH1 channel azimuths X = 0 to 360 in degrees (X is bearing from N):
            #             Rotate the two horizontal channels to find the radial component R
            #                 (R is the vector sum of the 2 horizontal channels in the back azimuth direction)
            #                 Assume BHE/BH2 is 90 degrees clockwise from BHN/BH1.
            #             Calculate the cross-correlation of R and H{Z} at zero lag:
            #                 Szr = sum(i): [R[t(i)] * H{Z[t(i)]}] where i = 1,...,N samples
            #             Calculate the auto-correlations of R and H{Z} at zero lag:
            #                 Szz = sum(i): [H{Z[t(i)]}^2] where i = 1,...,N samples
            #                 Srr = sum(i): [R[t(i)]^2] where i = 1,...,N samples
            #             Calculate and save 2 separate normalized correlation coefficients:
            #                 a) Czr = Szr / sqrt(Szz*Srr)
            #                 b) C*zr = Szr / Srr

            # Prefill Szz as it doesn't depend on the angle
            HZ_data = pd.Series(utils.get_slot(HZ,'data'))
            SzzValue = sum(HZ_data * HZ_data)
            Szz = [SzzValue] * 360
            Szr = [np.nan] * 360
            Srr = [np.nan] * 360

            # Calculate correlations as a function of angle
            rotateOK = True
            for angle in range(1,360,degreeIncrement):
                
                debug_point = 1
                
                # TODO: STOP DEVELOPMENT HERE
                # TODO:
                # TODO:  rotate2D is throwing errors about "object 'tr1' not found"
                # TODO:
                
                bop = irisseismic.rotate2D(stN, stE, angle)
                
                #result <- try(stR <- IRISSeismic::rotate2D(stN,stE,angle)[[1]], silent=TRUE)
                #if (class(result)[1] == "try-error") {
                    #setProcessExitCode( MCRWarning(paste("orientation_check skipping", sn.lId, "rotate2D returned an error. start=",halfHourStart,"end=", halfHourEnd)) )
                    #rotateOK <- FALSE
                #break
                #}
                #R <- stR@traces[[1]]
                #Srr[angle] <- sum( R@data *  R@data)
                #Szr[angle] <- sum(HZ@data *  R@data)
            #}
            #if (!rotateOK) {
                ## an error in the loop means we skip this SNL, go to next in loop
                #next
            #}
        
            ## Normalized correlation coefficients
            #Czr <- Szr / sqrt(Szz*Srr)
            #C_zr <- Szr / Szz
        
            #maxCzr <- max(Czr,na.rm=TRUE)
            #maxC_zr <- max(C_zr,na.rm=TRUE)
        
            #angleAtMaxCzr <- which(Czr == maxCzr)
            #angleAtMaxC_zr <- which(C_zr == maxC_zr)
        
            #azimuthR <- angleAtMaxC_zr %% 360
            #azimuthT <- (azimuthR + 90) %% 360

            
            
            # Now back to code 
            
            debug_point = 1


            #Szr <- vector("numeric",360)
            #Szz <- vector("numeric",360)
            #Srr <- vector("numeric",360)




















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
