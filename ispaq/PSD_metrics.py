
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
import pandas as pd
import fnmatch
from obspy.clients.fdsn import Client
from obspy import UTCDateTime
from .concierge import NoAvailableDataError
from . import utils
from . import irisseismic
from . import irismustangmetrics
from . import PDF_aggregator


#from astropy.io.ascii.tests.test_connect import files

def PSD_metrics(concierge):
    """
    Generate *PSD* metrics.

    :type concierge: :class:`~ispaq.concierge.Concierge`
    :param concierge: Data access expediter.

    :rtype: pandas dataframe
    :return: Dataframe of PSD metrics.

    .. rubric:: Example

    TODO:  doctest examples
    """
    # Get the logger from the concierge
    logger = concierge.logger
    
    # Default parameters 
    channelFilter = '.[HLGNPYXD].'
    logger.debug("channelFilter %s" % channelFilter)

    # function metadata dictionary
    function_metadata = concierge.function_by_logic['PSD']

    # Container for all of the metrics dataframes generated
    dataframes = []
    

    ####################
    def do_psd(concierge,starttime,endtime):
        try:
            availability = concierge.get_availability("PSDs", starttime=starttime,endtime=endtime)
        except NoAvailableDataError as e:
            raise
        except Exception as e:
            logger.debug(e)
            logger.error('concierge.get_availability() failed')
            return None

        # If the day has no data, then skip it (used to raise NoAvailableDataError)
        if availability is None:
            return

        # Apply the channelFilter and drop multiple metadata epochs
        availability = availability[availability.channel.str.contains(channelFilter)].drop_duplicates(['snclId'])
        # Loop over rows of the availability dataframe
        logger.info('Calculating PSD values for %d SNCLs on %s' % (availability.shape[0],str(starttime).split('T')[0]))

        for (index, av) in availability.iterrows():
            logger.info('%03d Calculating PSD values for %s' % (index, av.snclId))
            

            # Get the data ----------------------------------------------

            # NOTE:  Use the requested starttime and endtime
            try:
                r_stream = concierge.get_dataselect(av.network, av.station, av.location, av.channel,starttime,endtime, inclusiveEnd=False)
                if not utils.get_slot(r_stream, 'traces'):
                    # There is no data, just bypass it
                    continue
                try:
                    q = utils.get_slot(r_stream, "quality")
                except:
                    q = ""
                

            except Exception as e:
                #logger.debug(e)
                if str(e).lower().find('no data') > -1:
                    logger.info('No data available for %s' % (av.snclId))
                elif str(e).lower().find('multiple epochs') > -1:
                    logger.info('Skipping %s because multiple metadata epochs found' % (av.snclId))
                else:
                    logger.error(e)
                    #logger.warning('No data available for %s from %s' % (av.snclId, concierge.dataselect_url))
                continue

            # Run the PSD metric ----------------------------------------
            if any(key in function_metadata for key in ("PSD","PSDText")) :
                try:
                    evalresp = None
                    if (concierge.resp_dir):   # if resp_dir: run evalresp on local RESP file instead of web service
                        sampling_rate = utils.get_slot(r_stream, 'sampling_rate')
                        evalresp = utils.getSpectra(r_stream, sampling_rate, "PSD", concierge)
                    if (concierge.dataselect_type == "ph5ws"):
                        sampling_rate = utils.get_slot(r_stream, 'sampling_rate')
                        evalresp = utils.getSpectra(r_stream, sampling_rate, "PSD", concierge)
                    # get corrected PSD
                    try:
                        (df, PSDcorrected, PDF) = irismustangmetrics.apply_PSD_metric(concierge, r_stream, evalresp=evalresp)
                    except Exception as e:
                        raise

                    if not df.empty:
                        dataframes.append(df)

                    if "psd_corrected" in concierge.metric_names :
                        # Write out the corrected PSDs
                        # Do it this way to have each individual day file properly named with starttime.date
                        subFolder = '%s/%s/%s/' % (concierge.psd_dir, av.network, av.station)
                        if not q == "":
                            filename = '%s.%s_%s_PSDCorrected.csv' % (av.snclId, q, starttime.date)
                        else:
                            filename = '%s_%s_PSDCorrected.csv' % (av.snclId, starttime.date)
                        filepath = subFolder + filename
                        
                        if concierge.output == 'csv':
                            if not os.path.isdir(subFolder):
                                logger.info("psd_dir %s does not exist, creating directory" % subFolder)
                                os.makedirs(subFolder)
                            logger.info('Writing corrected PSD values to %s' % filepath)
                        
                        elif concierge.output == 'db':
                            logger.info('Writing corrected PSD values to %s' % concierge.db_name)

                        try:
                            # Add target
                            if not q == "":
                                PSDcorrected['target'] = '%s.%s' % (av.snclId, q)
                            else: 
                                PSDcorrected['target'] = av.snclId
                                
                            PSDcorrected.rename(columns={'freq':'frequency'}, inplace=True)
                            PSDcorrected = PSDcorrected[['target','starttime','endtime','frequency','power']]
                            utils.write_numeric_df(PSDcorrected, filepath, concierge, sigfigs=concierge.sigfigs)
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
            

    #########################
    def do_pdf(concierge, starttime, endtime):
        
        
#         fullFileList = list(); fullSnclList = list()
#         fileDF = pd.DataFrame(columns=["SNCL","FILE"], dtype="object")
        daylist = pd.date_range(start=str(starttime.date), end=str(endtime.date)).tolist()
        
        # Get a list of the files that exist in the directory within the sncl and timespan, or get psds from the database
        for sncl_pattern in concierge.sncl_patterns:
            logger.debug(sncl_pattern)
            fullFileList = list(); fullSnclList = list()
            fileDF = pd.DataFrame(columns=["SNCL","FILE"], dtype="object")
            
            # if using files on the filesystem
            if concierge.output == 'csv':
                logger.info("Looking for PSD values in CSV files")
            
                # We need to ignore the quality code, if included -- OUTDATED, we DO use quality code now
#                 if len(sncl_pattern.split('.')) == 5:
#                     sncl_pattern = sncl_pattern.rsplit('.', 1)[0]
                
                ## If no quality code is specified, then wildcard it
                if len(sncl_pattern.split('.')) == 4:
                    sncl_pattern = '%s.?,%s' % (sncl_pattern, sncl_pattern)
                    logger.info("No quality code specified, wildcarding it")    
                    
                    
                for day in daylist:
                    day = day.strftime("%Y-%m-%d")
                    files = []
                    for sncl_pat in sncl_pattern.split(','):
                        fnames = sncl_pat + "_" + str(day) + "_PSDCorrected.csv"
                        for root, dirnames, filenames in os.walk(concierge.psd_dir):
                            for filename in fnmatch.filter(filenames, fnames):
                                files.append(os.path.join(root, filename))
                    
                    #files = glob.glob(filename,recursive=True)
                    if files:
                        for file in files:
                            fullFileList.append(file)
                            fullSnclList.append(file.split('/')[-1].split('_')[0])
                    else:
                        logger.warning('No PSD files found for %s %s' % (sncl_pattern,day))
                            
                        
                
                fileDF['FILE'] = fullFileList
                fileDF['SNCL'] = fullSnclList            
                snclList = fileDF['SNCL'].unique()
                
                
                # Extract just the dates
                start = starttime.date
                end = endtime.date
                
        
                if start == end:
                    logger.info('Calculating PDFs for %d SNCLs on %s' % (snclList.shape[0],str(start)))
                else:
                    logger.info('Aggregating PDFs for %d SNCLs for %s through %s' % (snclList.shape[0],str(start), str(end)))
                    
                for (index, sncl) in enumerate(snclList):
                    logger.info('%03d Calculating PDF values for %s' % (index, sncl))
                        
                    [pdfDF,modesDF, maxDF, minDF] = PDF_aggregator.calculate_PDF(fileDF, sncl, starttime, endtime, concierge)

        
                    if ('plot' in concierge.pdf_type) and not pdfDF.empty:
                        PDF_aggregator.plot_PDF(sncl, starttime, endtime, pdfDF, modesDF, maxDF, minDF, concierge)
                        
                

                
            elif concierge.output == 'db':
                logger.debug("Looking for %s targets in %s PSD table for %s to %s" % (sncl_pattern, concierge.db_name, starttime.date, endtime.date))
                db_sncl_pattern = sncl_pattern.replace('*','%').replace('?','_')
                
                ## No longer required, since PSDs now have quality codes
#                 if len(db_sncl_pattern.split('.')) == 5:
#                     # TODO: In the future I'd like to be able to include quality codes in the PSDs
#                     db_sncl_pattern = db_sncl_pattern.rsplit('.', 1)[0]

                ## If no quality code is included in the preference file or command line SNCL definition, then add a wildcard for the quality code
                if len(db_sncl_pattern.split('.')) == 4:
                    db_sncl_pattern = ('%s*' % db_sncl_pattern).replace("*","%")
                    logger.info("No quality code specified, wildcarding it")
                
                # Retrieve all targets that match
                try:
                    snclList = utils.retrieve_psd_unique_targets(concierge.db_name, db_sncl_pattern, starttime, endtime, logger) 
                except Exception as e:
                    if "no such table" in str(e):
                        logger.warning("Unable to access table %s in %s" % (str(e).split(":")[1], concierge.db_name))
                    else:
                        logger.warning("Unable to access PSD values for %s %s - %s" % (sncl_pattern, starttime, endtime))
                    return "No Table"
                
                for (index, sncl) in enumerate(snclList):
                    logger.info('%03d Calculating PDF values for %s' % (index, sncl))
                    
                    [pdfDF,modesDF, maxDF, minDF] = PDF_aggregator.calculate_PDF("", sncl, starttime, endtime, concierge)

                    
                    
                    if ('plot' in concierge.pdf_type) and not pdfDF.empty:
                        PDF_aggregator.plot_PDF(sncl, starttime, endtime, pdfDF, modesDF, maxDF, minDF, concierge)
                        

            else:
                logger.info("Output %s not recognized: cannot find PSD values" % concierge.output)
        
        return 1
#             

    ########################

    # Loop over days and calculate PSDs and/or PDFs -----------------------

    if (concierge.resp_dir):   # if resp_dir: run evalresp on local RESP file instead of web service
        logger.info("Searching for response files in '%s'" % concierge.resp_dir)
    else:                   # try to connect to irisws/evalresp
        try:
            resp_url = Client("IRIS")
        except Exception as e:
            logger.error("Could not connect to 'http:/service.iris.edu/irisws/evalresp/1'")
            return None

    # ----- All available SNCLs -------------------------------------------------

    # Get date range
    start = concierge.requested_starttime
    end = concierge.requested_endtime
    # NEW: if more than one day, calculate both daily and full-timespan PSDs
    delta = (end.date - start.date).days
    nday=int(delta)+1
    
    # Calculate for entire span
    logger.info('Calculating noise metrics for %s to %s' % (str(start).split('T')[0],str(end).split('T')[0]))
    
    if any(key in function_metadata for key in ("PSD","PSDText")):

        if concierge.station_client is None:
            try:
                initialAvailability = concierge.get_availability("PSDs", starttime=start,endtime=end)
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

            if (endtime-1).date == end.date:
                endtime = end
            if starttime.date == start.date:
                starttime = start

            # Can't have a starttime that matches the end
            if starttime == end:
                continue
            
            do_psd(concierge,starttime, endtime)
                

    if ("pdf" in concierge.metric_names) and ('daily' in concierge.pdf_interval):
        logger.info("Calculating daily PDFs")

        for day in range(nday):
            
            # On the first and last days, use the hour provided, otherwise use 00:00:00
            starttime = (start + day * 86400)
            starttime = UTCDateTime(starttime.strftime("%Y-%m-%d") +"T00:00:00Z")
            endtime = starttime + 86400

            if (endtime-1).date == end.date:
                endtime = end
            if starttime.date == start.date:
                starttime = start
            
            # Can't have a starttime that matches the end
            if starttime == end:
                continue
            
            logger.info("Calculating daily PDFs for %s" % starttime.date)

            result = do_pdf(concierge, starttime, endtime-1)
            if result == "No Table":
                break
                
                 
    if ("pdf" in concierge.metric_names) and ('aggregated' in concierge.pdf_interval):
        logger.info("Calculating aggregated PDFs")
        result = do_pdf(concierge, start, end - 1)
    
    # Concatenate and filter dataframes before returning -----------------------

    if len(dataframes) == 0 and 'PSD' in function_metadata:
        logger.warning('"PSD" metric calculation generated zero metrics')
        return None

    else:

        # make a dummy data frame in the case of just creating PDF with no supporting DF statistics
        #result = pd.DataFrame({'metricName': ['PDF','PDF'], 'value': [0,1]})

        # Create a boolean mask for filtering the dataframe
        def valid_metric(x):
            return x in concierge.metric_names

        if 'PSD' in function_metadata:
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
