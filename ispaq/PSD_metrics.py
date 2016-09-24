"""
ISPAQ Business Logic for Simple Metrics.

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


def PSD_metrics(concierge):
    """
    Generate *PSD* metrics.

    :type concierge: :class:`~ispaq.concierge.Concierge`
    :param concierge: Data access expiditer.
    
    :rtype: pandas dataframe (TODO: change this)
    :return: Dataframe of PSD metrics. (TODO: change this)

    .. rubric:: Example

    TODO:  doctest examples
    """
    # Get the logger from the concierge
    logger = concierge.logger
    
    # Default parameters from IRISMustangUtils::generateMetrics_crossCorrelation or crossCorrelationMetrics_exec.R
    includeRestricted = False
    channelFilter = '.H.' # Gillian email on 9/8/16

    # Container for all of the metrics dataframes generated
    dataframes = []
    correctedPSDs = []
    PDFs = []

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
                logger.debug('No data for %s' % (av.snclId))
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

        if function_metadata.has_key('PSD'):
            try:
                (df, correctedPSD, PDF) = irismustangmetrics.apply_PSD_metric(r_stream)
                dataframes.append(df)
                # Write out the corrected PSDs
                filepath = concierge.output_file_base + "_" + av.snclId + "__correctedPSD.csv"
                logger.info('Writing corrected PSD to %s.' % os.path.basename(filepath))
                try:
                    utils.write_numeric_df(correctedPSD, filepath, sigfigs=concierge.sigfigs)
                except Exception as e:
                    logger.debug(e)
                    logger.error('Unable to write %s' % (filepath))
                    raise
                # Write out the PDFs
                filepath = concierge.output_file_base + "_" + av.snclId + "__PDF.csv"
                logger.info('Writing PDF to %s.' % os.path.basename(filepath))
                try:
                    utils.write_numeric_df(PDF, filepath, sigfigs=concierge.sigfigs)  
                except Exception as e:
                    logger.debug(e)
                    logger.error('Unable to write %s' % (filepath))
                    raise
            except Exception as e:
                logger.debug(e)
                logger.debug('"PSD" metric calculation failed for %s' % (av.snclId))
                continue
                
        # Run the PSD plot ------------------------------------------

        if function_metadata.has_key('PSDPlot'):
            try:  
                # TODO:  Use concierge to determine where to put the plots?
                starttime = utils.get_slot(r_stream, 'starttime')
                filename = '%s.%s_PDF.png' % (av.snclId, starttime.strftime('%Y.%j'))
                filepath = concierge.plot_output_dir + '/' + filename
                status = irismustangmetrics.apply_PSD_plot(r_stream, filepath)
            except Exception as e:
                logger.debug(e)
                logger.error('"PSD" plot generation failed for %s' % (av.snclId))
                    

    # Concatenate and filter dataframes before returning -----------------------

    if len(dataframes) == 0:
        logger.warn('"PSD" metric calculation generated zero metrics')
        return None
    else:
        # TODO:  Should we always add a dummy dataframe in cases where we only generate plots?
        result = pd.DataFrame({'metricName': 'DUMMY',
                               'value': 0,
                               'snclq': 'NET.STA.LOC.CHA.M',
                               'starttime': concierge.requested_starttime,
                               'endtime': concierge.requested_endtime,
                               'qualityFlag': -9},
                              index=[0])
            
        if function_metadata.has_key('PSD'):                    
            # Concatenate dataframes before returning ----------------------------------
            result = pd.concat(dataframes, ignore_index=True)    
            result.reset_index(drop=True, inplace=True)
            
        return(result)


# ------------------------------------------------------------------------------


if __name__ == '__main__':
    import doctest
    doctest.testmod(exclude_empty=True)
