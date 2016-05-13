# -*- coding: utf-8 -*-


"""ispaq.ispaq: provides entry point main()."""


__version__ = "0.5.0"


import argparse
import datetime
import logging
import os
import sys

from concierge import Concierge
from user_request import UserRequest
import irisseismic
import irismustangmetrics
import utils

from simple_metrics import simple_metrics
from SNR_metrics import SNR_metrics
from PSD_metrics import PSD_metrics

def main():

    # Parse arguments ----------------------------------------------------------
    
    parser = argparse.ArgumentParser(description=__doc__.strip())
    parser.add_argument('-V', '--version', action='version',
                        version='%(prog)s ' + __version__)
    parser.add_argument('--starttime', action='store', required=True,
                        help='starttime in ISO 8601 format')
    parser.add_argument('--endtime', action='store', required=False,
                        help='endtime in ISO 8601 format')
    parser.add_argument('-M', '--metrics', required=True,
                        help='name of metric to calculate')
    parser.add_argument('-S', '--sncls', action='store', default=False,
                        help='Network.Station.Location.Channel identifier (e.g. US.OXF..BHZ)')
    parser.add_argument('-P', '--preferences-file', default=os.path.expanduser('./preference_files/cleandemo.txt'),
                        type=argparse.FileType('r'), help='location of preference file')
    parser.add_argument('-O', '--output-loc', default='.',
                        help='location to output ')
    parser.add_argument('--log-level', action='store', default='DEBUG',
                        choices=['DEBUG','INFO','WARNING','ERROR','CRITICAL'],
                        help='log level printed to console')

    # TODO:  additional configurable elements like sigfigs should be in the preferences file
    # parser.add_argument('--sigfigs', type=check_negative, default=6,
    #                     help='number of significant figures to round metrics to')

    args = parser.parse_args(sys.argv[1:])
    
    # Set up logging -----------------------------------------------------------
    
    # Full DEBUG level logging goes to TRANSCRIPT.txt
    # Console logging level is set by the '--log-level' argument
    
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    
    fh = logging.FileHandler('TRANSCRIPT.txt', mode='w')
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(formatter)
    logger.addHandler(fh)
    
    ch = logging.StreamHandler()
    ch.setLevel(getattr(logging, args.log_level))
    ch.setFormatter(formatter) 
    logger.addHandler(ch)


    logger.debug('Running ISPAQ version %s on %s' % (__version__, datetime.datetime.now().strftime('%c')))


    #     Create UserRequest object     ---------------------------------------
    #
    # The UserRequest class is in charge of parsing arguments issued on the
    # command line, loading and parsing a preferences file, and setting a bunch
    # of properties that capture the totality of what the user wants in a single
    # invocation of the ISPAQ top level script.

    logger.debug('Creating UserRequest ...')
    try:
        user_request = UserRequest(args, logger=logger)
    except Exception as e:
        if str(e) == "Not really an error.":
            pass
        else:
            raise

    #     Create Concierge (aka Expediter)     ---------------------------------
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
        logger.critical(e)
        raise


    #     Generate Simple Metrics     ------------------------------------------

    if 'simple' in concierge.logic_types:
        logger.debug('Inside simple business logic ...')
        try:
            simple_df = simple_metrics(concierge)
            try:
                filepath = concierge.output_file_base + "__simpleMetrics.csv"
                logger.info('Writing simple metrics to %s.\n' % os.path.basename(filepath))
                simple_df = utils.format_simple_df(simple_df, sigfigs=6)
                simple_df.to_csv(filepath)
            except Exception as e:
                logger.error(e)
        except Exception as e:
            logger.error(e)


    # Generate SNR Metrics -----------------------------------------------------

    if 'SNR' in concierge.logic_types:
        logger.debug('Inside SNR business logic ...')
        try:
            SNR_df = SNR_metrics(concierge)
            try:
                filepath = concierge.output_file_base + "__SNRMetrics.csv"
                logger.info('Writing SNR metrics to %s.\n' % os.path.basename(filepath))
                SNR_df = utils.format_simple_df(SNR_df, sigfigs=6)
                SNR_df.to_csv(filepath)
            except Exception as e:
                logger.error(e)
        except Exception as e:
            logger.error(e)


    # Generate PSD Metrics -----------------------------------------------------

    if 'PSD' in concierge.logic_types:
        logger.debug('Inside PSD business logic ...')
        try:
            PSD_df = PSD_metrics(concierge)
            try:
                filepath = concierge.output_file_base + "__PSDMetrics.csv"
                logger.info('Writing PSD metrics to %s.\n' % os.path.basename(filepath))
                PSD_df = utils.format_simple_df(PSD_df, sigfigs=6)
                PSD_df.to_csv(filepath)
            except Exception as e:
                logger.error(e)
        except Exception as e:
            logger.error(e)


    #    # Generate [increasingly complex/time-consuming metrics] -------------------
    #
    #    #try:
    #      #complex_output = ispaq.business_logic.complex_metrics(concierge)
    #      #try:
    #          ## Dump output to a file
    #      #except:
    #          ##
    #    #except:
    #          ##


    logger.info('ALL FINISHED!')


# ------------------------------------------------------------------------------

if __name__ == "__main__":
    main()
