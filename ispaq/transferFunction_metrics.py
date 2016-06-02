"""
ISPAQ Business Logic for transfer Metrics.

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

import itertools # for combintations

def transferFunction_metrics(concierge):
    """
    Generate *transfer* metrics.

    :type concierge: :class:`~ispaq.concierge.Concierge`
    :param concierge: Data access expiditer.

    :rtype: pandas dataframe
    :return: Dataframe of simple metrics.

    .. rubric:: Example

    TODO:  doctest examples
    """
    # Get the logger from the concierge
    logger = concierge.logger

    # Container for all of the metrics dataframes generated
    dataframes = []

    # ----- All available SNCLs -------------------------------------------------
    
    availability = concierge.get_availability()

    # function metadata dictionary
    function_metadata = concierge.function_by_logic['transferFunction']

    # Find the locations associated with seismic channels
    channels = sorted(set(availability.channel))
    
    ############################################################
    # Loop through all channels looking for multiple locations.
    ############################################################

    for channel in channels:
        
        channelAvailability = availability[availability.channel == channel]
        
        # Bail if there is only one location
        if channelAvailability.shape[0] == 1:
            continue
        
        # NOTE:  channelAvailability is a dataframe with one row per location for the current SN.L
        # NOTE:  Now we use itertools.combinations to generate all combinations of locations of rows.
        
        rowMatrix = []
        for combo in itertools.combinations(range(channelAvailability.shape[0]), 2):
            rowMatrix.append(combo)
        
        # Convert to a numpy matrix for total agreement with original R code
        rowMatrix = np.matrix(rowMatrix)
              
        ############################################################
        # Loop through all location pairs for this channel
        ############################################################

        for i in range(rowMatrix.shape[0]):
            
            av1 = channelAvailability.iloc[rowMatrix[i,0],]
            av2 = channelAvailability.iloc[rowMatrix[i,1],]
        
            # Only continue if azimuths are within 5 degrees of eachother
            azimuthAngle = abs(av1.azimuth - av2.azimuth) * math.pi/180.0
            maxAzimuthAngle = 5.0 * math.pi/180.0
            if (math.cos(azimuthAngle) < math.cos(maxAzimuthAngle)):
                logger.debug('\tskipping %s:%s because azimuths differ by more than 5 degrees' % (av1.snclId, av2.snclId))
                continue
        
            # Only continue if dips are within 5 degrees of eachother
            dipAngle = abs(av1.dip - av2.dip) * math.pi/180.0
            maxDipAngle = 5.0 * math.pi/180.0
            if (math.cos(dipAngle) < math.cos(maxDipAngle)):
                logger.debug('\tskipping %s:%s because dips differ by more than 5 degrees' % (av1.snclId, av2.snclId))
                continue
        
            # Channels OK so proceed
        
            try:
                r_stream1 = concierge.get_dataselect(av1.network, av1.station, av1.location, av1.channel)
            except Exception as e:
                logger.warning('\tunable to obtain data for %s from %s: %s' % (av1.snclId, concierge.dataselect_url, e))
                continue
            
            try:
                r_stream2 = concierge.get_dataselect(av2.network, av2.station, av2.location, av2.channel)
            except Exception as e:
                logger.warning('\tunable to obtain data for %s from %s: %s' % (av2.snclId, concierge.dataselect_url, e))
                continue
            
            
            # Run the transferFunction metric ----------------------------------------
    
            logger.info('Calculating transferFunction metrics for %s:%s' % (av1.snclId, av2.snclId))
            try:
                df = irismustangmetrics.apply_correlation_metric(r_stream1, r_stream2, 'transferFunction')
                # By default, this metrics returns value="N". Convert this to NaN
                df.value = np.NaN
                dataframes.append(df)
            except Exception as e:
                logger.error('"transfer_function" metric calculation failed for %s:%s: %s' % (av1.snclId, av2.snclId, e))
                
        
        # END of location-pairs loop
        
        
    # END of channel loop
            

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
