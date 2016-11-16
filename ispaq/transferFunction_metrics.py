"""
ISPAQ Business Logic for transfer Metrics.

:copyright:
    Mazama Science
:license:
    GNU Lesser General Public License, Version 3
    (http://www.gnu.org/copyleft/lesser.html)
"""

from __future__ import (absolute_import, division, print_function)

import itertools # for combintations
import os
import math
import numpy as np
import pandas as pd

from obspy import UTCDateTime

from .concierge import NoAvailableDataError

from . import utils
from . import irisseismic
from . import irismustangmetrics
from . import evalresp as evresp


class EvalrespException(Exception):
    pass


# ------------------------------------------------------------------------------
#      BEGIN Utility Function
#
def getTransferFunctionSpectra(st, sampling_rate, respDir=None):
    # This function returns an evalresp fap response for trace st using sampling_rate 
    # to determine frequency limits
    #
    # set respDir to the directory containing RESP files to run evalresp locally

    # Min and Max frequencies for evalresp will be those used for the cross spectral binning
    alignFreq = 0.1

    if (sampling_rate <= 1):
        loFreq = 0.001
    elif (sampling_rate > 1 and sampling_rate < 10):
        loFreq = 0.0025
    else:
        loFreq = 0.005

    # No need to exceed the Nyquist frequency after decimation
    hiFreq = 0.5 * sampling_rate

    log2_alignFreq = math.log(alignFreq,2)
    log2_loFreq = math.log(loFreq,2)
    log2_hiFreq = math.log(hiFreq,2)
    
    if alignFreq >= hiFreq:
        octaves = []
        octave = log2_alignFreq
        while octave >= log2_loFreq:
            if octave <= log2_hiFreq:
                octaves.append(octave)
            octave -= 0.125
        octaves = pd.Series(octaves).sort_values().reset_index(drop=True)
            
    else:
        octaves = []
        octave = log2_alignFreq
        loOctaves = []
        while octave >= log2_loFreq:
            loOctaves.append(octave)
            octave -= 0.125
        loOctaves = pd.Series(loOctaves)
            
        octave = log2_alignFreq
        hiOctaves = []
        while octave <= log2_hiFreq:
            hiOctaves.append(octave)
            octave += 0.125
        hiOctaves = pd.Series(hiOctaves)
            
        octaves = loOctaves.append(hiOctaves).drop_duplicates().sort_values().reset_index(drop=True)
        
    binFreq = pow(2,octaves)

    # Arguments for evalresp
    minfreq = min(binFreq)
    maxfreq = max(binFreq)
    nfreq = len(binFreq)
    units = 'DEF'
    output = 'FAP'

    network = utils.get_slot(st,'network')
    station = utils.get_slot(st,'station')
    location = utils.get_slot(st,'location')
    channel = utils.get_slot(st,'channel')
    starttime = utils.get_slot(st,'starttime')
  
    #print("DEBUG: minfreq: %f, maxfreq: %f, nfreq: %d" % (minfreq,maxfreq,nfreq))
    # REC - invoke evalresp either programmatically from a RESP file or by invoking the web service 
    if (respDir):
        # calling local evalresp -- generate the target file based on the SNCL identifier
        # the file pattern is RESP.<NET>.<STA>.<LOC>.<CHA>
        localFile = os.path.join(respDir,".".join(["RESP", network, station, location, channel])) # attempt to find the RESP file
        #print("DEBUG: Local evalresp invocation on file: %s..." % localFile)
        if (os.path.exists(localFile)):
            debugMode = False
            evalResp = evresp.getEvalresp(localFile, network, station, location, channel, starttime,
                                       minfreq, maxfreq, nfreq, units.upper(), output.upper(), "LOG", debugMode)
        else:
            raise EvalrespException('WARNING: No RESP file found at %s for evalresp' % (localFile))
    else:    
        # calling the web service 
        #print("DEBUG: calling evalresp web service on %s" % ",".join([network,station,location,channel]))
        evalResp = irisseismic.getEvalresp(network, station, location, channel, starttime,
                                       minfreq, maxfreq, nfreq, units.lower(), output.lower())
    #print(evalResp)   # VERBOSE DEBUG -- turn off for production use
    return(evalResp)

#
#      END Utility Function
# ------------------------------------------------------------------------------


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

    # Default parameters from IRISMustangUtils::generateMetrics_transferFunction or transferFunctionMetrics_exec.R
    channelFilter = '[FCHBML][HN].' # Mary Templeton email on 2016-08-26
    
    # Container for all of the metrics dataframes generated
    dataframes = []

    # ----- All available SNCLs -------------------------------------------------
    
    try:
        availability = concierge.get_availability()
    except NoAvailableDataError as e:
        raise
    except Exception as e:
        logger.debug(e)
        logger.error('concierge.get_availability() failed with an unknown error')
        return None
    
    # Apply the channelFilter
    availability = availability[availability.channel.str.contains(channelFilter)]      

    # function metadata dictionary
    function_metadata = concierge.function_by_logic['transferFunction']

    # Get unique network-station pairs
    networkStationPairs = availability.network + '.' + availability.station
    networkStationPairs = networkStationPairs.drop_duplicates().sort_values().reset_index(drop=True)
    
    for networkStation in networkStationPairs:
 
        logger.debug("transferFn - %s..." % networkStation)
        # Subset the availability dataframe to contain only results for this networkStation
        (network,station) = networkStation.split('.')
        stationAvailability = availability[(availability.network == network) & (availability.station == station)].reset_index(drop=True)

        # Do not include any sncls that lack metadata
        metaMask = stationAvailability.dip.isnull().values 
        metaMask = metaMask == False
        logger.debug("metaMask: %s" % ",".join(str(x) for x in metaMask))
        stationAvailability = stationAvailability[metaMask]

	if stationAvailability.shape[0] == 0:
            logger.info('Network-Station %s.%s has data, but no metadata, skipping.' % (network, station))
	    continue
	else:
            logger.info('Network-Station pair %s.%s has %d channels' % (network, station, stationAvailability.shape[0]))
        
        ##################################################################
        # Loop through all channels by dip looking for multiple locations.
        ##################################################################
    
        # Vertical and Horizontal channels will be handled differently
        dips = stationAvailability.dip.abs().drop_duplicates().sort_values().reset_index(drop=True)
    
        for dip in dips:
    
            logger.info('Working on dip %f' % (dip))
    
            # Find channels with the current dip
            channelAvailability = stationAvailability[abs(stationAvailability.dip) == dip].reset_index(drop=True)
    
            # Treat vertical channels as we've always done
            if dip == 90:
    
                # Bail if there is only one Z channel
                if channelAvailability.shape[0] <= 1:
                    logger.debug('Skipping %s because there are no other channels for comparison' % (channelAvailability.snclId[0]))
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
                    
                    Zav1 = channelAvailability.iloc[rowMatrix[i,0],]
                    Zav2 = channelAvailability.iloc[rowMatrix[i,1],]

                    # We don't want to compare 2 sample rates from the same instrument.
                    # We'll define the same instrument as one where the location code 
                    # and last 2 characters of the channel code match.
                    if ( (Zav1.location == Zav2.location) and (Zav1.channel[1:] == Zav2.channel[1:]) ):
                        continue
                
                
                    # Get primary (1) and secondary (2) traces
                    try:
                        Zst1 = concierge.get_dataselect(Zav1.network, Zav1.station, Zav1.location, Zav1.channel, inclusiveEnd=False)
                    except Exception as e:
                        if str(e).lower().find('no data') > -1:
                            logger.warning('No data for %s' % (Zav1.snclId))
                        else:
                            logger.warning('No data for %s from %s: %s' % (Zav1.snclId, concierge.dataselect_url, e))
                        continue
                    
                    try:
                        Zst2 = concierge.get_dataselect(Zav2.network, Zav2.station, Zav2.location, Zav2.channel, inclusiveEnd=False)
                    except Exception as e:
                        if str(e).lower().find('no data') > -1:
                            logger.warning('No data for %s' % (Zav2.snclId))
                        else:
                            logger.warning('No data for %s from %s: %s' % (Zav2.snclId, concierge.dataselect_url, e))
                        continue
                    
                    sampling_rate = min(utils.get_slot(Zst1,'sampling_rate'), utils.get_slot(Zst2,'sampling_rate'))
                
                    # Get primary (1), secondary (2) and orthogonal secondary spectra 
                    try:
                        Zevalresp1 = getTransferFunctionSpectra(Zst1,sampling_rate,concierge.resp_dir)
                        Zevalresp2 = getTransferFunctionSpectra(Zst2,sampling_rate,concierge.resp_dir) 
                    except Exception as e:
                        logger.debug('"transferFunction_metrics" getTransferFunctionSpectra failed for %s:%s: %s' % (av1.snclId, av2.snclId, e))
                        continue
                    
                
                    # Run the transferFunction metric ----------------------------------------
            
                    logger.debug('Calculating transferFunction metrics for %s:%s' % (Zav1.snclId, Zav2.snclId))
                    try:
                        df = irismustangmetrics.apply_correlation_metric(Zst1, Zst2, 'transferFunction', Zevalresp1, Zevalresp2)
                        dataframes.append(df)
                    except Exception as e:
                        logger.debug('"transfer_function" metric calculation failed for %s:%s: %s' % (Zav1.snclId, Zav2.snclId, e))
                    
                # END of for i (pairs) in rowMatrix

            elif dip == 0:
                
                # If azimuths don't agree for primary and secondary horizontal channels, 
                # we will first rotate secondary channels to match primary channels.
        
                # Bail if there are only two horizontal channels
                if channelAvailability.shape[0] <= 2:
                    logger.debug('Skipping %s because there are no other channels for comparison' % (channelAvailability.snclId[0]))
                    continue
                 
                # Convert snclId into a snclPrefix that excludes the last character
                # Matching scnlPrefixes should be orthogonal Y and X channel pairs
                channelAvailability['snclPrefix'] = channelAvailability.snclId.str[:-1]
                snclPrefixes = channelAvailability.snclPrefix.drop_duplicates().sort_values().reset_index(drop=True)
        
                # Make sure we've sorted by snclPrefix before we loop through and assign X or Y to each entry
                channelAvailability = channelAvailability.sort_values(by='snclPrefix')

                # We're labeling orthogonal horizontal channels "Y" and "X" based on the Cartesian coordinate system
                # If we need to rotate the secondary channels, we'll need this information
                axisList = []
                for snclPrefix in snclPrefixes:
                    xyAvailability = channelAvailability[channelAvailability.snclId.str.contains(snclPrefix)]
                    logger.debug("xyAvailability has %d rows" % xyAvailability.shape[0])
                    # This should never happen, but just in case...
                    if xyAvailability.shape[0] <= 0:
                        continue
                    
                    # Channel with no orthogonal mate - we can use it straight, but we can't rotate it
                    # We'll mark the axis "U" for unknown
                    if xyAvailability.shape[0] == 1:
                        axisList.append('U')
                    
                    # END if 1 row
        
                    # Found an orthogonal channel pair - label X and Y channels
                    if xyAvailability.shape[0] == 2:
                        azim1 = xyAvailability.azimuth.iloc[0]
                        azim2 = xyAvailability.azimuth.iloc[1]
                        diffAzim = azim1 - azim2
        
                        if ( (diffAzim >= -93 and diffAzim <= -87) or (diffAzim >= 267 and diffAzim <= 273) ):
                            axisList.append("Y")
                            axisList.append("X")
                        elif ( (diffAzim >= -273 and diffAzim <= -267) or (diffAzim >= 87 and diffAzim <= 93) ):
                            axisList.append("X")
                            axisList.append("Y")      
                        else:
                            # These channels are mates, but they're not orthogonal enough 
                            # Use them individually if possible, but don't attempt to rotate them 
                            # Since they're not technically X and Y we'll mark both "U" (unknown) as well
                            axisList.append("U")
                            axisList.append("U")

                    # END if 2 rows     
        
                    # Hard telling why there are so many channels, so mark them "D" for drop
                    # Metadata errors can cause cases like this
                    if xyAvailability.shape[0] >= 3:
                        for i in range(xyAvailability.shape[0]):
                            axisList.append("D")

                    # END if 3 or more rows
        
                # END for snclPrefixes
        
                # Add a "cartAxis" column to the horizontal channel availability data frame
                channelAvailability["cartAxis"] = axisList
        
                # Drop entries marked "D"
                channelAvailability = channelAvailability[channelAvailability.cartAxis != "D"].reset_index(drop=True)
        
                # Separate channel availability data frame into X and Y data frames 
                # Pair them across location codes
                XchannelAvailability = channelAvailability[channelAvailability.cartAxis != "Y"].reset_index(drop=True)
                YchannelAvailability = channelAvailability[channelAvailability.cartAxis != "X"].reset_index(drop=True)
        
                XrowMatrix = []
                for combo in itertools.combinations(range(XchannelAvailability.shape[0]), 2):
                    XrowMatrix.append(combo)
                
                # Convert to a pandas dataframe
                XrowMatrix = pd.DataFrame(XrowMatrix,columns=['Primary','Secondary'])
        
                YrowMatrix = []
                for combo in itertools.combinations(range(YchannelAvailability.shape[0]), 2):
                    YrowMatrix.append(combo)
                
                # Convert to a numpy matrix for total agreement with original R code
                YrowMatrix = pd.DataFrame(YrowMatrix,columns=['Primary','Secondary'])
                
                # Determine the difference in azimuth between primary and secondary channels for X and Y
                # Create a column called "azDiff" to store this difference
                azDiffList = []
                for i in range(XrowMatrix.shape[0]):
                    azDiff = XchannelAvailability.azimuth[XrowMatrix.iloc[i,0]] - XchannelAvailability.azimuth[XrowMatrix.iloc[i,1]]
                    if (azDiff < 0):
                        azDiff = azDiff + 360
                    azDiffList.append(azDiff)
                    
                XrowMatrix['azDiff'] = azDiffList                   
                    
                azDiffList = []
                for i in range(YrowMatrix.shape[0]):
                    azDiff = YchannelAvailability.azimuth[YrowMatrix.iloc[i,0]] - YchannelAvailability.azimuth[YrowMatrix.iloc[i,1]]
                    if (azDiff < 0):
                        azDiff = azDiff + 360
                    azDiffList.append(azDiff)
                    
                YrowMatrix['azDiff'] = azDiffList   
        
                # Separate pairs into those that need rotating and those that don't
                YrowMatrixRot = YrowMatrix[YrowMatrix.azDiff != 0].reset_index(drop=True)
                YrowMatrixNoRot = YrowMatrix[YrowMatrix.azDiff == 0].reset_index(drop=True)
                XrowMatrixRot = XrowMatrix[XrowMatrix.azDiff != 0].reset_index(drop=True)
                XrowMatrixNoRot = XrowMatrix[XrowMatrix.azDiff == 0].reset_index(drop=True)

                matrixListToRotate = (YrowMatrixRot, XrowMatrixRot)
                matrixListNotToRotate = (YrowMatrixNoRot, XrowMatrixNoRot)
                availabilityList = (YchannelAvailability, XchannelAvailability)
        
                # Get traces, spectra and transfer functions for horizontal channels that don't need rotating
                # First Y channels, then X
                for i in range(2):
        
                    if matrixListNotToRotate[i].shape[0] != 0:
        
                        for j in range(matrixListNotToRotate[i].shape[0]):
        
                            av1 = availabilityList[i].iloc[int(matrixListNotToRotate[i].iloc[j,0]),]
                            av2 = availabilityList[i].iloc[int(matrixListNotToRotate[i].iloc[j,1]),]
        
                            # We don't want to compare 2 sample rates from the same instrument.
                            # We'll define the same instrument as one where the location code 
                            # and last 2 characters of the channel code match.
                            if ( (av1.location == av2.location) and (av1.channel[:-1] == av2.channel[:-1]) ):
                                continue
        
                            # Get primary (1) and secondary (2) traces
                            try:
                                st1 = concierge.get_dataselect(av1.network, av1.station, av1.location, av1.channel, inclusiveEnd=False)
                            except Exception as e:
                                if str(e).lower().find('no data') > -1:
                                    logger.warning('No data for %s' % (av1.snclId))
                                else:
                                    logger.warning('No data for %s from %s: %s' % (av1.snclId, concierge.dataselect_url, e))
                                continue
        
                            try:
                                st2 = concierge.get_dataselect(av2.network, av2.station, av2.location, av2.channel, inclusiveEnd=False)
                            except Exception as e:
                                if str(e).lower().find('no data') > -1:
                                    logger.warning('No data for %s' % (av2.snclId))
                                else:
                                    logger.warning('No data for %s from %s: %s' % (av2.snclId, concierge.dataselect_url, e))
                                continue
        
                            sampling_rate = min( utils.get_slot(st1, 'sampling_rate'), utils.get_slot(st2, 'sampling_rate') )
        
                            # Get primary (1), secondary (2) and orthogonal secondary spectra
                            try:
                                evalresp1 = getTransferFunctionSpectra(st1, sampling_rate, concierge.resp_dir)
                                evalresp2 = getTransferFunctionSpectra(st2, sampling_rate, concierge.resp_dir)
                            except Exception as e:
                                logger.debug('"transferFunction_metrics" getTransferFunctionSpectra failed for %s:%s: %s' % (av1.snclId, av2.snclId, e))
                                continue
                                
        
                            # Calculate the metrics and append them to the current list
                            logger.debug('Calculating transferFunction metrics for %s:%s' % (av1.snclId, av2.snclId))
                            try:
                                df = irismustangmetrics.apply_transferFunction_metric(st1, st2, evalresp1, evalresp2)
                            except Exception as e:
                                logger.debug('"transfer_function" metric calculation failed for %s:%s: %s' % (av1.snclId, av2.snclId, e))
                                continue
                           
                            ##logger.debug("append dataframe: %s" % str(df)) 
                            dataframes.append(df)

                        # END for rows (pairs) in matrix
        
                    # END if matrix has rows
        
                # END for lists of pairs we don't need to rotate
        
        
        
                # Get traces, spectra and transfer functions for horizontal channels that DO need rotating
                for i in range(2):
        
                    if matrixListToRotate[i].shape[0] != 0:
        
                        for j in range(matrixListToRotate[i].shape[0]):
             
                            av1 = availabilityList[i].iloc[int(matrixListToRotate[i].iloc[j,0]),]   # Primary trace for Y (i=1) or X (i=2)
                            av2 = availabilityList[i].iloc[int(matrixListToRotate[i].iloc[j,1]),]   # Secondary trace for Y (i=1) or X (i=2)
        
                            # We don't want to compare 2 sample rates from the same instrument.
                            # We'll define the same instrument as one where the location code 
                            # and last 2 characters of the channel code match.
                            if ( (av1.location == av2.location) and (av1.channel[:-1] == av2.channel[:-1]) ):
                                continue
        
                            # Orthogonal mate of av2 - we assume they will have matching snclPrefixes
                            if i == 0:
                                av3 = availabilityList[i+1][availabilityList[i+1].snclPrefix == av2.snclPrefix]
                            else:
                                av3 = availabilityList[i-1][availabilityList[i-1].snclPrefix == av2.snclPrefix]
                                
                            # We need to have exactly 1 orthogonal trace for rotation
                            if av3.shape[0] != 1:
                                continue
                            else:
                                av3 = av3.iloc[0,] # convert from DataFrame to Series
        
                            rotAngle = matrixListToRotate[i].iloc[j,2]
        
                            # Get primary (1), secondary (2), and secondary orthogonal traces
                            try:
                                st1 = concierge.get_dataselect(av1.network, av1.station, av1.location, av1.channel, inclusiveEnd=False)
                            except Exception as e:
                                if str(e).lower().find('no data') > -1:
                                    logger.warning('No data for %s' % (av1.snclId))
                                else:
                                    logger.warning('No data for %s from %s: %s' % (av1.snclId, concierge.dataselect_url, e))
                                continue
        
                            try:
                                st2 = concierge.get_dataselect(av2.network, av2.station, av2.location, av2.channel, inclusiveEnd=False)
                            except Exception as e:
                                if str(e).lower().find('no data') > -1:
                                    logger.warning('No data for %s' % (av2.snclId))
                                else:
                                    logger.warning('No data for %s from %s: %s' % (av2.snclId, concierge.dataselect_url, e))
                                continue
                             
                            try:
                                st3 = concierge.get_dataselect(av3.network, av3.station, av3.location, av3.channel, inclusiveEnd=False)
                            except Exception as e:
                                if str(e).lower().find('no data') > -1:
                                    logger.warning('No data for %s' % (av3.snclId))
                                else:
                                    logger.warning('No data for %s from %s: %s' % (av3.snclId, concierge.dataselect_url, e))
                                continue
                             
                            sampling_rate = min( utils.get_slot(st1, 'sampling_rate'), utils.get_slot(st2, 'sampling_rate') )
        
                            # Get primary (1), secondary (2) and orthogonal secondary spectra 
                            try:
                                evalresp1 = getTransferFunctionSpectra(st1, sampling_rate, concierge.resp_dir)
                                evalresp2 = getTransferFunctionSpectra(st2, sampling_rate, concierge.resp_dir)          
                                evalresp3 = getTransferFunctionSpectra(st3, sampling_rate, concierge.resp_dir)
                            except Exception as e:
                                logger.debug('"transferFunction_metrics" getTransferFunctionSpectra failed for %s:%s: %s' % (av1.snclId, av2.snclId, e))
                                continue
                            
        
                            # Determine which secondary trace is Y vs. X
                            if av2.cartAxis == "Y":
                                Yst2 = st2
                                Xst2 = st3
                                Yevalresp2 = evalresp2
                                Xevalresp2 = evalresp3
                            elif av2.cartAxis == "X":
                                Yst2 = st3
                                Xst2 = st2
                                Yevalresp2 = evalresp3
                                Xevalresp2 = evalresp2
                            else:
                                continue
        
                            # Rotate the secondary traces
                            try:
                                traceRotList = irisseismic.rotate2D(Yst2, Xst2, rotAngle)
                            except Exception as e:
                                logger.debug('Trace rotation failed: %s' % (e))
                                continue
                            
                            RYst2 = traceRotList[0]
                            RXst2 = traceRotList[1]
        
                            # Rotate the secondary spectra
                            radians = rotAngle * math.pi/180.0
        
                            RYevalresp2 = Yevalresp2
                            RXevalresp2 = Xevalresp2
        
                            # sin**2(rotAngle) + cos**2(rotAngle) = 1
                            RYevalresp2.amp = (math.cos(radians))**2 * Yevalresp2.amp + (math.sin(radians))**2 * Xevalresp2.amp
                            RXevalresp2.amp = (-1.0 * math.sin(radians))**2 * Yevalresp2.amp + (math.cos(radians))**2 * Xevalresp2.amp

                            # Determine whether primary trace was X or Y
                            if av1.cartAxis == "Y":
                                logger.debug('Calculating transferFunction metrics for %s:%s' % (av1.snclId, av2.snclId))
                                try:
                                    df = irismustangmetrics.apply_transferFunction_metric(st1, RYst2, evalresp1, RYevalresp2)
                                except Exception as e:
                                    logger.debug('"transfer_function" metric calculation failed for %s:%s: %s' % (av1.snclId, av2.snclId, e))
                                    continue
                                
                                dataframes.append(df)
                                
                            elif av1.cartAxis == "X":
                                logger.debug('Calculating transferFunction metrics for %s:%s' % (av1.snclId, av2.snclId))
                                try:
                                    df = irismustangmetrics.apply_transferFunction_metric(st1, RXst2, evalresp1, RXevalresp2)
                                except Exception as e:
                                    logger.debug('"transfer_function" metric calculation failed for %s:%s: %s' % (av1.snclId, av2.snclId, e))
                                    continue
                                
                                dataframes.append(df)                            
                                
                        # END of for location pairs in matrix
        
                    # END if matrix has rows
        
                # END for lists of pairs we DO rotate
        
            else:

                # Write warning if dip are neither vertical nor horizontal.
                # They would require 3D rotation that isn't available here.
                logger.debug('Skipping %s -- dip %f  requires 3D rotation' % (channelAvailability.snclId.iloc[i], channelAvailability.dip.iloc[i]))
        
            # END of if dip = ...
            
        # END for dips
          
    # END for stations    
        
    if len(dataframes) == 0:
        logger.warn('"transfer_function" metric calculation generated zero metrics')
        return None
    else:
        result = pd.concat(dataframes, ignore_index=True)
        result.reset_index(drop=True, inplace=True)
        return(result)


# ------------------------------------------------------------------------------


if __name__ == '__main__':
    import doctest
    doctest.testmod(exclude_empty=True)
