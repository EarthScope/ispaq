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
import numpy as np
import pandas as pd

from obspy import UTCDateTime

from .concierge import NoAvailableDataError

from . import utils
from . import irisseismic
from . import irismustangmetrics
from . import transferFunction_metrics as transfn


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
    channelFilter = '.[HNL].' 

    # Container for all of the metrics dataframes generated
    dataframes = []

    # ----- All UN-available SNCLs ----------------------------------------------

    # TODO:  Anything to do here?

    # ----- All available SNCLs -------------------------------------------------

    try:
        availability = concierge.get_availability()
    except NoAvailableDataError as e:
        raise
    except Exception as e:
        logger.debug(e)
        logger.error('concierge.get_availability() failed with an unknown exception')
        return None

    # Apply the channelFilter
    availability = availability[availability.channel.str.contains(channelFilter)]      

    # function metadata dictionary
    function_metadata = concierge.function_by_logic['PSD']
    
    logger.info('Calculating PSD metrics for %d SNCLs.' % (availability.shape[0]))
    
    # Loop over rows of the availability dataframe
    for (index, av) in availability.iterrows():
                
        logger.info('%03d Calculating PSD metrics for %s' % (index, av.snclId))

        # Get the data ----------------------------------------------

        # NOTE:  Use the requested starttime, not just what is available
        try:
            r_stream = concierge.get_dataselect(av.network, av.station, av.location, av.channel)
        except Exception as e:
            logger.debug(e)
            if str(e).lower().find('no data') > -1:
                logger.warning('No data for %s' % (av.snclId))
            else:
                logger.warning('No data for %s from %s' % (av.snclId, concierge.dataselect_url))
            # TODO:  Add empty dataframe ???
            #df = pd.DataFrame({'metricName': 'percent_available',
                               #'value': 0,
                               #'snclq': av.snclId + '.M',
                               #'starttime': concierge.requested_starttime,
                               #'endtime': concierge.requested_endtime,
                               #'qualityFlag': -9},
                              #index=[0]) 
            #dataframes.append(df)
            continue


        # Run the PSD metric ----------------------------------------

        if any(key in function_metadata for key in ("PSD","PSDText")) :
            try:
                evalresp = None
                if (concierge.resp_dir):   # if resp_dir: run evalresp on local RESP file instead of web service
                    logger.debug("Accessing local RESP file...")
                    evalresp = transfn.getTransferFunctionSpectra(r_stream, av.samplerate, concierge.resp_dir)
                # get corrected PSDs
                logger.debug("apply_PSD_metric...")
                (df, PSDCorrected, PDF) = irismustangmetrics.apply_PSD_metric(r_stream, evalresp=evalresp)
                dataframes.append(df)

                if "psd_corrected" in concierge.metric_names :
                # Write out the corrected PSDs
                    filepath = concierge.output_file_base + "_" + av.snclId + "__PSDCorrected.csv"
                    logger.info('Writing corrected PSD text to %s.' % os.path.basename(filepath))
                    try:
                        utils.write_numeric_df(PSDCorrected, filepath, sigfigs=concierge.sigfigs)
                    except Exception as e:
                        logger.debug(e)
                        logger.error('Unable to write %s' % (filepath))
                        raise
                if "pdf_text" in concierge.metric_names :
                # Write out the PDFs
                    filepath = concierge.output_file_base + "_" + av.snclId + "__PDF.csv"
                    logger.info('Writing PDF text to %s.' % os.path.basename(filepath))
                    try:
                        # Add target, start- and endtimes
                        PDF['target'] = av.snclId
                        PDF['starttime'] = concierge.requested_starttime
                        PDF['endtime'] = concierge.requested_endtime
                        utils.write_numeric_df(PDF, filepath, sigfigs=concierge.sigfigs)  
                    except Exception as e:
                        logger.debug(e)
                        logger.error('Unable to write %s' % (filepath))
                        raise
            except Exception as e:
                logger.warning(e)
                logger.warning('"PSD" metric calculation failed for %s' % (av.snclId))
                continue
                
        # Run the PSD plot ------------------------------------------

        if 'PSDPlot' in function_metadata :
            try:  
                # TODO:  Use concierge to determine where to put the plots?
                starttime = utils.get_slot(r_stream, 'starttime')
                filename = '%s.%s_PDF.png' % (av.snclId, starttime.strftime('%Y.%j'))
                filepath = concierge.plot_output_dir + '/' + filename
                evalresp = None
                if (concierge.resp_dir):   # if resp_dir: run evalresp on local RESP file instead of web service
                    logger.debug("Accessing local RESP file...")
                    evalresp = transfn.getTransferFunctionSpectra(r_stream, av.samplerate, concierge.resp_dir)
                status = irismustangmetrics.apply_PSD_plot(r_stream, filepath, evalresp=evalresp)
                logger.info('Writing PDF plot %s.' % os.path.basename(filepath))
            except Exception as e:
                logger.warning(e)
                logger.warning('"PSD" plot generation failed for %s' % (av.snclId))
                    

    # Concatenate and filter dataframes before returning -----------------------

    if len(dataframes) == 0 and 'PSD' in function_metadata:
        logger.warn('"PSD" metric calculation generated zero metrics')
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
