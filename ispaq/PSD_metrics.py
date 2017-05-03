"""
ISPAQ Business Logic for PSD Metrics.

:copyright:
    Mazama Science
:license:
    GNU Lesser General Public License, Version 3
    (http://www.gnu.org/copyleft/lesser.html)
"""

from __future__ import (absolute_import, division, print_function)

import os
import math
import pandas as pd

from obspy.clients.fdsn import Client
from obspy import UTCDateTime

from .concierge import NoAvailableDataError

from . import utils
from . import irisseismic
from . import irismustangmetrics

def PSD_metrics(concierge):
    """
    Generate *PSD* metrics.

    :type concierge: :class:`~ispaq.concierge.Concierge`
    :param concierge: Data access expediter.
    
    :rtype: pandas dataframe (TODO: change this)
    :return: Dataframe of PSD metrics. (TODO: change this)

    .. rubric:: Example

    TODO:  doctest examples
    """
    # Get the logger from the concierge
    logger = concierge.logger
    
    # Default parameters 
    channelFilter = '.*'

    # function metadata dictionary
    function_metadata = concierge.function_by_logic['PSD']

    # Container for all of the metrics dataframes generated
    dataframes = []

    if (concierge.resp_dir):   # if resp_dir: run evalresp on local RESP file instead of web service
        logger.info("Searching for response files in '%s'" % concierge.resp_dir)
    else:                   # try to connect to irisws/evalresp
        try:
            resp_url = Client("IRIS")
        except Exception as e:
            logger.error("Could not connect to 'http:/service.iris.edu/evalresp'")
            return None

    # ----- All available SNCLs -------------------------------------------------

    # NEW: Loop over days
    start = concierge.requested_starttime
    end = concierge.requested_endtime

    delta = (end-start)/(24*60*60)
    nday=int(delta)+1

    if nday > 1 and concierge.station_client is None:
        try:
            initialAvailability = concierge.get_availability(starttime=start,endtime=end)
        except NoAvailableDataError as e:
            raise
        except Exception as e:
            logger.error("concierge.get_availability() failed: '%s'" % e)
            return None

    for day in range(nday):
        # On the first and last days, use the hour provided, otherwise use 00:00:00
        starttime = (start + day * 86400)
        starttime = UTCDateTime(starttime.strftime("%Y-%m-%d") +"T00:00:00Z")
        endtime = starttime + 86400

        if starttime == end:
            continue

        try:
            availability = concierge.get_availability(starttime=starttime,endtime=endtime)
        except NoAvailableDataError as e:
            raise
        except Exception as e:
            logger.debug(e)
            logger.error('concierge.get_availability() failed')
            return None


        # If the day has no data, then skip it (used to raise NoAvailableDataError)
        if availability is None:
            continue

        # Apply the channelFilter and drop multiple metadata epochs
        availability = availability[availability.channel.str.contains(channelFilter)].drop_duplicates(['snclId'])      

        # Loop over rows of the availability dataframe
        logger.info('Calculating PSD metrics for %d SNCLs on %s' % (availability.shape[0],str(starttime).split('T')[0]))

        for (index, av) in availability.iterrows():
            logger.info('%03d Calculating PSD metrics for %s' % (index, av.snclId))

            # Get the data ----------------------------------------------

            # NOTE:  Use the requested starttime and endtime
            try:
                r_stream = concierge.get_dataselect(av.network, av.station, av.location, av.channel,starttime,endtime)
            except Exception as e:
                logger.debug(e)
                if str(e).lower().find('no data') > -1:
                    logger.info('No data available for %s' % (av.snclId))
                elif str(e).lower().find('multiple epochs') :
                    logger.info('Skipping %s because multiple metadata epochs found' % (av.snclId))
                else:
                    logger.warning('No data available for %s from %s' % (av.snclId, concierge.dataselect_url))
                continue

            # Run the PSD metric ----------------------------------------

            if any(key in function_metadata for key in ("PSD","PSDText")) :
                try:
                    evalresp = None
                    if (concierge.resp_dir):   # if resp_dir: run evalresp on local RESP file instead of web service
                        sampling_rate = utils.get_slot(r_stream, 'sampling_rate')
                        evalresp = utils.getSpectra(r_stream, sampling_rate, concierge)

                    # get corrected PSDs
                    try:
                        (df, PSDcorrected, PDF) = irismustangmetrics.apply_PSD_metric(r_stream, evalresp=evalresp)
                    except Exception as e:
                        raise
                    dataframes.append(df)

                    if "psd_corrected" in concierge.metric_names :
                        # Write out the corrected PSDs
                        # Do it this way to have each individual day file properly named with starttime.date
                        file_base_psd = '%s_%s_%s' % (concierge.user_request.requested_metric_set,
                                                      concierge.user_request.requested_sncl_set,
                                                      starttime.date)
                        filepath = concierge.csv_dir + '/' + file_base_psd + "_" + av.snclId + "_PSDcorrected.csv"
                        logger.info('Writing corrected PSD to %s' % os.path.basename(filepath))
                        try:
                            # Add target
                            PSDcorrected['target'] = av.snclId
                            PSDcorrected = PSDcorrected[['target','starttime','endtime','freq','power']]
                            utils.write_numeric_df(PSDcorrected, filepath, sigfigs=concierge.sigfigs)
                        except Exception as e:
                            logger.debug(e)
                            logger.error('Unable to write %s' % (filepath))
                            raise

                    if "pdf_text" in concierge.metric_names :
                    # Write out the PDFs
                        filepath = concierge.csv_dir + '/' + file_base_psd + "_" + av.snclId + "_PDF.csv"
                        logger.info('Writing PDF text to %s.' % os.path.basename(filepath))
                        try:
                            # Add target, start- and endtimes
                            PDF['target'] = av.snclId
                            PDF['starttime'] = starttime
                            PDF['endtime'] = endtime
                            PDF = PDF[['target','starttime','endtime','freq','power','hits']]
                            utils.write_numeric_df(PDF, filepath, sigfigs=concierge.sigfigs)  
                        except Exception as e:
                            logger.debug(e)
                            logger.error('Unable to write %s' % (filepath))
                            raise

                except Exception as e:
                    if str(e).lower().find('could not resolve host: service.iris.edu') > -1:
                        logger.debug(e)
                        logger.error('getEvalresp failed to find service.iris.edu')
                    elif str(e).lower().find('no psds returned') > -1:
                        logger.warning("IRISMustangMetrics: No PSDs returned for %s" % (av.snclId))
                    else:
                        logger.error(e)
                    logger.warning('"PSD" metric calculation failed for %s' % (av.snclId))
                    continue



            # Run the PSD plot ------------------------------------------

            if 'PSDPlot' in function_metadata :
                try:  
                    filename = '%s.%s_PDF.png' % (av.snclId, starttime.date)
                    filepath = concierge.png_dir + '/' + filename
                    evalresp = None
                    if (concierge.resp_dir):   # if resp_dir: run evalresp on local RESP file instead of web service
                        sampling_rate = utils.get_slot(r_stream, 'sampling_rate')
                        evalresp = utils.getSpectra(r_stream, sampling_rate, concierge)
                    status = irismustangmetrics.apply_PSD_plot(r_stream, filepath, evalresp=evalresp)
                    logger.info('Writing PDF plot %s.' % os.path.basename(filepath))
                except Exception as e:
                    if str(e).lower().find('no psds returned') > -1:
                        logger.warning("IRISMustangMetrics: No PSDs returned for %s" % (av.snclId))
                    else:
                        logger.warning(e)
                    logger.warning('"PSD" plot generation failed for %s' % (av.snclId))
                    
    # Concatenate and filter dataframes before returning -----------------------

    if len(dataframes) == 0 and 'PSD' in function_metadata:
        logger.warning('"PSD" metric calculation generated zero metrics')
        return None

    else:
        # make a dummy data frame in the case of just creating PSDPlots with no supporting DF statistics
        result = pd.DataFrame({'metricName': ['PSDPlot','PSDPlot'], 'value': [0,1]})

        # Create a boolean mask for filtering the dataframe
        def valid_metric(x):
            return x in concierge.metric_names

        if function_metadata.has_key('PSD'):                    
            # Concatenate dataframes before returning ----------------------------------
            result = pd.concat(dataframes, ignore_index=True)    
            mask = result.metricName.apply(valid_metric)
            result = result[(mask)]
            result.reset_index(drop=True, inplace=True)
            
        return(result)


# ------------------------------------------------------------------------------


if __name__ == '__main__':
    import doctest
    doctest.testmod(exclude_empty=True)
