# -*- coding: utf-8 -*-


"""ispaq.ispaq: provides entry point main()."""

from __future__ import (absolute_import, division, print_function)

# Basic modules
import os
import sys
import argparse
import datetime
import logging

__version__ = "0.8.0x"


def main():

    # Parse arguments ----------------------------------------------------------
    
    default_preference_file = './preference_files/default.txt'  # we will use this pref file if one is not specified
    
    parser = argparse.ArgumentParser(description=__doc__.strip())
    parser.add_argument('-V', '--version', action='version',
                        version='%(prog)s ' + __version__)
    parser.add_argument('--starttime', action='store', required=False,
                        help='starttime in ISO 8601 format')
    parser.add_argument('--endtime', action='store', required=False,
                        help='endtime in ISO 8601 format')
    parser.add_argument('-M', '--metrics', required=False,
                        help='metric alias, defined in preference file')
    parser.add_argument('-S', '--stations', action='store', required=False,
                        help='stations alias, defined in preference file')
    parser.add_argument('-P', '--preferences-file', default=os.path.expanduser('./preference_files/default.txt'),
                        type=argparse.FileType('r'), help='path to preference file')
    parser.add_argument('--log-level', action='store', default='INFO',
                        choices=['DEBUG','INFO','WARNING','ERROR','CRITICAL'],
                        help='log level printed to console')
    parser.add_argument('-A', '--append', action='store_true', default=True,
                        help='append to TRANSCRIPT file rather than overwriting')
    parser.add_argument('-U', '--update-r', action='store_true', default=False,
                        help='check CRAN for more recent IRIS Mustang R package versions')

    try:
        args = parser.parse_args(sys.argv[1:])
    except IOError, msg:
        parser.error(str(msg))   # we may encounter an error accessing the indicated file
        raise SystemExit
    
    # Set up logging -----------------------------------------------------------
    
    # Full DEBUG level logging goes to ISPAQ_TRANSCRIPT.log
    # Console logging level is set by the '--log-level' argument
    
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    
    if args.append:
        fh = logging.FileHandler('ISPAQ_TRANSCRIPT.log', mode='a')
    else:
        fh = logging.FileHandler('ISPAQ_TRANSCRIPT.log', mode='w')

    fh.setLevel(logging.DEBUG)
    fh.setFormatter(formatter)
    logger.addHandler(fh)
    
    ch = logging.StreamHandler()
    ch.setLevel(getattr(logging, args.log_level))
    ch.setFormatter(formatter) 
    logger.addHandler(ch)

    logger.info('Running ISPAQ version %s on %s\n' % (__version__, datetime.datetime.now().strftime('%c')))


    # Validate the args --------------------------------------------------------
    
    # We can't use required=True in argpase because folks should be able to type only -U
    
    if not args.update_r:
        # start and end times
        if args.starttime is None:
            logger.critical('argument --starttime is required')
            raise SystemExit
    
        # metric sets
        if args.metrics is None:
            logger.critical('argument -M/--metrics is required')
            raise SystemExit
            
        # stations sets
        if args.stations is None:
            logger.critical('argument -S/--stations is required')
            raise SystemExit
    
    
    # Handle R package upgrades ------------------------------------------------
    
    if args.update_r:
        logger.info('Checking for IRIS R package updates...')
        from . import updater
        df = updater.get_IRIS_package_versions(logger)
        # TODO: Decide on proper behavior and output when updating R packages
        print('\n%s\n' % df)
        updater.update_IRIS_packages(logger)
        sys.exit(0)

    # Load additional modules --------------------------------------------------

    # These are loaded here so that asking for --verion or --help is bogged down
    # by the slow-to-load modules that require matplotlib

    # ISPAQ modules
    from .user_request import UserRequest
    from .concierge import Concierge, NoAvailableDataError
    from . import irisseismic
    from . import irismustangmetrics
    from . import utils
    
    # Specific ISPAQ business logic
    from .simple_metrics import simple_metrics
    from .SNR_metrics import SNR_metrics
    from .PSD_metrics import PSD_metrics
    from .crossTalk_metrics import crossTalk_metrics
    from .pressureCorrelation_metrics import pressureCorrelation_metrics
    from .crossCorrelation_metrics import crossCorrelation_metrics
    from .orientationCheck_metrics import orientationCheck_metrics
    from .transferFunction_metrics import transferFunction_metrics


    # Create UserRequest object ------------------------------------------------
    #
    # The UserRequest class is in charge of parsing arguments issued on the
    # command line, loading and parsing a preferences file, and setting a bunch
    # of properties that capture the totality of what the user wants in a single
    # invocation of the ISPAQ top level script.

    logger.debug('Creating UserRequest ...')
    try:
        user_request = UserRequest(args, logger=logger)
    except Exception as e:
        logger.debug(e)
        logger.critical("Failed to create UserRequest object")
        raise SystemExit


    # Create Concierge (aka Expediter) -----------------------------------------
    #
    # The Concierge class uses the completely filled out UserRequest and has the
    # job of expediting requests for information that may be made by any of the
    # business_logic methods. The goal is to have business_logic methods that can
    # be written as clearly as possible without having to know about the intricacies
    # of ObsPy.
  
    logger.debug('Creating Concierge ...')
    try:
        concierge = Concierge(user_request=user_request, logger=logger)
    except Exception as e:
        logger.debug(e)
        logger.critical("Failed to create Concierge object")
        raise SystemExit

    # Generate Simple Metrics --------------------------------------------------

    if 'simple' in concierge.logic_types:
        logger.debug('Inside simple business logic ...')
        try:
            df = simple_metrics(concierge)
            if df is None:
                logger.info('No simple metrics were calculated')
            else:
                try:
                    filepath = concierge.output_file_base + "_simpleMetrics.csv"
                    logger.info('Writing simple metrics to %s\n' % os.path.basename(filepath))
                    utils.write_simple_df(df, filepath, sigfigs=concierge.sigfigs)
                except Exception as e:
                    logger.debug(e)
                    logger.error("Error writing metric results")
        except NoAvailableDataError as e:
            logger.info("No data available for 'simple' metrics")
        except Exception as e:
            logger.debug(e)
            logger.error("Error calculating 'simple' metrics")


    # Generate SNR Metrics -----------------------------------------------------

    if 'SNR' in concierge.logic_types:
        logger.debug('Inside SNR business logic ...')
        try:
            df = SNR_metrics(concierge)
            if df is None:
                logger.info('No SNR metrics were calculated')
            else:
                try:
                    filepath = concierge.output_file_base + "_SNRMetrics.csv"
                    logger.info('Writing SNR metrics to %s\n' % os.path.basename(filepath))
                    utils.write_simple_df(df, filepath, sigfigs=concierge.sigfigs)
                except Exception as e:
                    logger.debug(e)
                    logger.error("Error writing metric results")
        except NoAvailableDataError as e:
            logger.info("No data available for 'SNR' metrics")
        except Exception as e:
            logger.debug(e)
            logger.error("Error calculating 'SNR' metrics")


    # Generate PSD Metrics -----------------------------------------------------

    if 'PSD' in concierge.logic_types:
        logger.debug('Inside PSD business logic ...')
        try:
            df = PSD_metrics(concierge)
            if df is None:
                logger.info('No PSD metrics were calculated')
            elif df.metricName[0] == 'PSDPlot':
                pass
            else:
                try:
                    # Write out the metrics
                    filepath = concierge.output_file_base + "_PSDMetrics.csv"
                    logger.info('Writing PSD metrics to %s\n' % os.path.basename(filepath))
                    utils.write_simple_df(df, filepath, sigfigs=concierge.sigfigs)
                except Exception as e:
                    logger.debug(e)
                    logger.error("Error writing metric results")
        except NoAvailableDataError as e:
            logger.info("No data available for 'PSD' metrics")
        except Exception as e:
            logger.debug(e)
            logger.error("Error calculating 'PSD' metrics")


    # Generate Cross Talk Metrics ----------------------------------------------

    if 'crossTalk' in concierge.logic_types:
        logger.debug('Inside crossTalk business logic ...')
        try:
            df = crossTalk_metrics(concierge)
            if df is None:
                logger.info('No crossTalk metrics were calculated.')
            else:
                try:
                    filepath = concierge.output_file_base + "_crossTalkMetrics.csv"
                    logger.info('Writing crossTalk metrics to %s\n' % os.path.basename(filepath))
                    utils.write_simple_df(df, filepath, sigfigs=concierge.sigfigs)
                except Exception as e:
                    logger.debug(e)
                    logger.error("Error writing metric results")
        except NoAvailableDataError as e:
            logger.info("No data available for 'crossTalk' metrics")
        except Exception as e:
            logger.debug(e)
            logger.error("Error calculating 'crossTalk' metrics")
        

    # Generate Pressure Correlation Metrics ----------------------------------------------

    if 'pressureCorrelation' in concierge.logic_types:
        logger.debug('Inside pressureCorrelation business logic ...')
        try:
            df = pressureCorrelation_metrics(concierge)
            if df is None:
                logger.info('No pressureCorrelation metrics were calculated')
            else:
                try:
                    filepath = concierge.output_file_base + "_pressureCorrelationMetrics.csv"
                    logger.info('Writing pressureCorrelation metrics to %s\n' % os.path.basename(filepath))
                    utils.write_simple_df(df, filepath, sigfigs=concierge.sigfigs)
                except Exception as e:
                    logger.debug(e)
                    logger.error("Error writing metric results")
        except NoAvailableDataError as e:
            logger.info("No data available for 'pressureCorrelation' metrics")
        except Exception as e:
            logger.debug(e)
            logger.error("Error calculating 'pressureCorrelation' metrics")
        

    # Generate Cross Correlation Metrics ---------------------------------------

    if 'crossCorrelation' in concierge.logic_types:
        logger.debug('Inside crossCorrelation business logic ...')
        try:
            df = crossCorrelation_metrics(concierge)
            if df is None:
                logger.info('No crossCorrelation metrics were calculated')
            else:
                try:
                    filepath = concierge.output_file_base + "_crossCorrelationMetrics.csv"
                    logger.info('Writing crossCorrelation metrics to %s\n' % os.path.basename(filepath))
                    utils.write_simple_df(df, filepath, sigfigs=concierge.sigfigs)
                except Exception as e:
                    logger.debug(e)
                    logger.error("Error writing metric results")
        except NoAvailableDataError as e:
            logger.info("No data available for 'crossCorrelation' metrics")
        except Exception as e:
            logger.debug(e)
            logger.error("Error calculating 'crossCorrelation' metrics")
                

    # Generate Orientation Check Metrics ---------------------------------------

    if 'orientationCheck' in concierge.logic_types:
        logger.debug('Inside orientationCheck business logic ...')
        try:
            df = orientationCheck_metrics(concierge)
            if df is None:
                logger.info('No orientationCheck metrics were calculated')
            else:
                try:
                    filepath = concierge.output_file_base + "_orientationCheckMetrics.csv"
                    logger.info('Writing orientationCheck metrics to %s\n' % os.path.basename(filepath))
                    utils.write_simple_df(df, filepath, sigfigs=concierge.sigfigs)
                except Exception as e:
                    logger.debug(e)
                    logger.error("Error writing metric results")
        except NoAvailableDataError as e:
            logger.info("No data available for 'orientationCheck' metrics")
        except Exception as e:
            logger.debug(e)
            logger.error("Error calculating 'orientationCheck' metrics")
                        
                        
    # Generate Transfer Function Metrics ---------------------------------------

    if 'transferFunction' in concierge.logic_types:
        logger.debug('Inside transferFunction business logic ...')
        try:
            df = transferFunction_metrics(concierge)
            if df is None:
                logger.info('No transferFunction metrics were calculated')
            else:
                try:
                    filepath = concierge.output_file_base + "_transferMetrics.csv"
                    logger.info('Writing transfer metrics to %s\n' % os.path.basename(filepath))
                    utils.write_simple_df(df, filepath, sigfigs=concierge.sigfigs)
                except Exception as e:
                    logger.debug(e)
                    logger.error("Error writing metric results")
        except NoAvailableDataError as e:
            logger.info("No data available for 'transferFunction' metrics")
        except Exception as e:
            logger.debug(e)
            logger.error("Error calculating 'transferFunction' metrics")


    logger.info('ALL FINISHED!')


# ------------------------------------------------------------------------------

if __name__ == "__main__":
    main()
