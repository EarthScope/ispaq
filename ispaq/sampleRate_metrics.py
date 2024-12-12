
"""
ISPAQ Business Logic for sampleRate Metrics.

:copyright:
    Mazama Science
:license:
    GNU Lesser General Public License, Version 3
    (https://www.gnu.org/copyleft/lesser.html)
"""

import os
import pandas as pd

import obspy
from distutils.version import StrictVersion

from . import utils
from . import irisseismic
from . import irismustangmetrics

from obspy.clients.fdsn import Client
from obspy import UTCDateTime
from .concierge import NoAvailableDataError

def sampleRate_metrics(concierge):
    """
    Generate *sampleRate* metrics.

    :type concierge: :class:`~ispaq.concierge.Concierge`
    :param concierge: Data access expediter.

    :rtype: pandas dataframe
    :return: Dataframe of sampleRate metrics.

    .. rubric:: Example

    TODO:  doctest examples
    """
    # Get the logger from the concierge
    logger = concierge.logger
    
    # Default parameters 
    channelFilter = '[BCDEFGHLMSVU][HPNLG][0-9ENZRT]|B[XY][12Z]|HX[12Z]'
    logger.debug("channelFilter %s" % channelFilter)

    # function metadata dictionary
    function_metadata = concierge.function_by_logic['sampleRate']

    # Container for all of the metrics dataframes generated
    dataframes = []
    
    start = concierge.requested_starttime
    end = concierge.requested_endtime
    delta = (end-start)/(24*60*60)
    nday=int(delta)+1

    if concierge.station_client is None:
        try:
            initialAvailability = concierge.get_availability("sample_rates", starttime=start,endtime=end)
        except NoAvailableDataError as e:
            raise
        except Exception as e:
            logger.error("concierge.get_availability() failed: '%s'" % e)
            return None
        
    for day in range(nday):
        starttime = (start + day * 86400)
        starttime = UTCDateTime(starttime.strftime("%Y-%m-%d") + "T00:00:00Z")
        endtime = starttime + 86400

        if starttime == end:
            continue

        try:
            availability = concierge.get_availability("sample_rates", starttime=starttime, endtime=endtime)
        except NoAvailableDataError as e:
            raise
        except Exception as e:
            logger.debug(e)
            logger.error('concierge.get_availability() failed')
            return None 

        # If the day has no data, then skip it (used to raise NoAvailableDataError)
        if availability is None:
            logger.debug("skipping %s with no available data" % (starttime.date))
            continue

        # Apply the channelFilter and drop multiple metadata epochs
        availability = availability[availability.channel.str.contains(channelFilter)].drop_duplicates(['snclId'])
        # Loop over rows of the availability dataframe
        logger.info('Calculating sampleRate values for %d SNCLs on %s' % (availability.shape[0],str(starttime).split('T')[0]))

        for (index, av) in availability.iterrows():
            logger.info('%03d Calculating sampleRate values for %s' % (index, av.snclId))

            # Get the data ----------------------------------------------
            # NOTE:  Use the requested starttime and endtime
            try:
                r_stream = concierge.get_dataselect(av.network, av.station, av.location, av.channel,starttime,endtime, inclusiveEnd=False)
            except Exception as e:
                logger.debug(e)
                if str(e).lower().find('no data') > -1:
                    logger.info('No data available for %s' % (av.snclId))
                elif str(e).lower().find('multiple epochs') > -1:
                    logger.info('Skipping %s because multiple metadata epochs found' % (av.snclId))
                else:
                    logger.warning('No data available for %s from %s' % (av.snclId, concierge.dataselect_url))
                continue

            # Run the sampleRate metrics ----------------------------------------

            if 'sample_rate_resp' in concierge.metric_names:
                try:
                    evalresp = None
                    sampling_rate = utils.get_slot(r_stream, 'sampling_rate')
                    norm_freq = utils.get_slot(r_stream, 'SensitivityFrequency')
                    resp_pct = 15 # % deviation allowed between response-derived sample rate and miniseed sample rate

                    if (concierge.resp_dir):   # if resp_dir: run evalresp on local RESP file instead of web service
                        logger.debug('sampling_rate %f', sampling_rate)
                        logger.debug('norm_freq %f', norm_freq)
                        evalresp = utils.getSampleRateSpectra(r_stream, sampling_rate, norm_freq, concierge)     #getSampleRateSpectra uses concierge to know where to find the resp info
#                         logger.debug(print(evalresp))
                    try:
                        df1 = irismustangmetrics.apply_sampleRateResp_metric(r_stream, resp_pct, norm_freq, evalresp)
                    except Exception as e:
                        raise

                    if not df1.empty:
                        dataframes.append(df1)
                
                except Exception as e:
                    if str(e).lower().find('could not resolve host: service.earthscope.org') > -1:
                        logger.debug(e)
                        logger.error('getEvalresp failed to find service.earthscope.org')
                    else:
                        logger.error(e)
                    logger.warning('sampleRateResp metric calculation failed for %s' % (av.snclId))
                    continue
            
            if 'sample_rate_channel' in concierge.metric_names:
                try:
                    chan_rate = av.samplerate     # metadata sample rate
                    channel_pct = 1  # % deviation allowed between metadata sample rate and miniseed sample rate

                    df2 = irismustangmetrics.apply_sampleRateChannel_metric(r_stream, channel_pct, chan_rate)

                    if not df2.empty:
                        dataframes.append(df2)

                except Exception as e:
                    logger.error(e)
                    logger.warning('sampleRateResp channel calculation failed for %s' % (av.snclId))
                    continue

 
    if len(dataframes) == 0:
        logger.warning('"sampleRate" metric calculation generated zero metrics')
        return None

    else:
        # Create a boolean mask for filtering the dataframe
        def valid_metric(x):
            return x in concierge.metric_names

        try:
            # Concatenate dataframes before returning ----------------------------------
            result = pd.concat(dataframes, ignore_index=True)
            mask = result.metricName.apply(valid_metric)
            result = result[(mask)]
            result.reset_index(drop=True, inplace=True)
            return(result)
        except Exception as e:
            logger.info(e)
            return(None)
# ------------------------------------------------------------------------------


if __name__ == '__main__':
    import doctest
    doctest.testmod(exclude_empty=True)
