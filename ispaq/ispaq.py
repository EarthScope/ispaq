# -*- coding: utf-8 -*-


"""ispaq.ispaq: provides entry point main()."""

from __future__ import (absolute_import, division, print_function)

# Basic modules
import os
import sys
import imp
import argparse
import datetime
import logging
import numpy as np
import subprocess
from _ast import Try
from numpy.random import sample

__version__ = "3.1.0-beta"

# dictionary of currently defined ISPAQ metric groups and business logic
# for comparison with R package IRISMustangMetrics/ISPAQUtils.R json

def currentispaq():
    # The metrics that are inside of each of these (ex basicStats) is defined in ISPAQUtils.R and returned in the function getMetricFunctionMetadata
    groups = {'simple': ['basicStats','gaps','numSpikes','STALTA','stateOfHealth','maxRange'],
              'SNR': ['SNR'],
              'PSD': ['PSD','PSDText','PDF'],
              'crossCorrelation': ['crossCorrelation'],
              'crossTalk': ['crossTalk'],
              'orientationCheck': ['orientationCheck'],
              'pressureCorrelation': ['pressureCorrelation'],
              'transferFunction': ['transferFunction'],
              'sampleRate': ['sampleRateResp','sampleRateChannel'] }
    return groups

def main():
    
    # Check our Conda environment ----------------------------------------------
    # let's check for our primary supporting python modules
    try:
        imp.find_module('rpy2')
        imp.find_module('obspy')
        imp.find_module('pandas')
    except ImportError as e:
        print('ERROR: please activate your ispaq environment before running: %s' % e)
        raise SystemExit
        
    # Parse arguments ----------------------------------------------------------
    
    epilog_text='If no preference file is specified and the default file ./preference_files/default.txt cannot be found:\n--csv_dir, pdf_dir, and psd_dir default to "."\n--sncl_format defaults to "N.S.C.L"\n--sigfigs defaults to "6"\n--pdf_type defaults to "plot,text"\n--pdf_interval defaults to "aggregated"\n--plot_include defaults to "colorbar,legend"'
    parser = argparse.ArgumentParser(description=" ".join(["ISPAQ version",__version__]), epilog=epilog_text,formatter_class=lambda prog: argparse.RawTextHelpFormatter(prog,max_help_position=35,width=82))
    parser._optionals.title = "single arguments"

    metrics = parser.add_argument_group('arguments for running metrics')
    metrics.add_argument('-P', '--preferences-file', required=False, help='path to preference file, default=./preference_files/default.txt')
    metrics.add_argument('-M', '--metrics', required=False,
                        help='single Metrics alias as defined in preference file, or one or \nmore metric names in a comma-separated list, required')
    metrics.add_argument('-S', '--stations', required=False,
                        help='single Station_SNCLs alias as defined in preference file, or \none or more SNCL[Q] in a comma-separated list, required.\nnotes: SNCL[Q] refers to Station.Network.Channel.Location.(optional)Quality\n       If using wildcarding, enclose in quotation marks')
    metrics.add_argument('--starttime', required=False,
                        help='starttime in ObsPy UTCDateTime format, required for webservice requests \nand defaults to earliest data file for local data \nexamples: YYYY-MM-DD, YYYYMMDD, YYYY-DDD, YYYYDDD[THH:MM:SS]')
    metrics.add_argument('--endtime',  required=False,
                        help='endtime in ObsPy UTCDateTime format, default=starttime + 1 day; \nif starttime is also not specified then it defaults to the latest data \nfile for local data \nexamples: YYYY-MM-DD, YYYYMMDD, YYYY-DDD, YYYYDDD[THH:MM:SS]')
   
   
    prefs = parser.add_argument_group('optional arguments for overriding preference file entries')
    prefs.add_argument('--dataselect_url', required=False,
                        help='FDSN webservice or path to directory with miniSEED files')
    prefs.add_argument('--station_url', required=False,
                        help='FDSN webservice or path to stationXML file')
    prefs.add_argument('--event_url', required=False,
                        help='FDSN webservice or path to QuakeML file')
    prefs.add_argument('--resp_dir', required=False,
                        help='path to directory with RESP files')
    prefs.add_argument('--output', required=False,
                       help='write metrics to csv file (csv) or sqlite database file (db). Options: csv, db')
    prefs.add_argument('--db_name', required=False,
                       help='name of sqlite database file, if output=csv')
    prefs.add_argument('--csv_dir', required=False,
                        help='directory to write generated metrics .csv files, if output=csv')
    prefs.add_argument('--psd_dir', required=False,
                        help='directory to write/read existing PSD .csv files, if output=csv')
    prefs.add_argument('--pdf_dir', required=False,
                        help='directory to write generated PDF files')
    prefs.add_argument('--pdf_type', required=False,
                        help='output format of generated PDFs - text and/or plot')
    prefs.add_argument('--pdf_interval', required=False,
                        help='time span for PDFs - daily and/or aggregated over the entire span')
    prefs.add_argument('--plot_include', required=False,
                        help='PDF plot graphics options - legend, colorbar, and/or fixed_yaxis_limits, \nor none')
    prefs.add_argument('--sncl_format', required=False,
                        help='format of SNCL aliases and miniSEED file names \nexamples:"N.S.L.C","S.N.L.C"\nwhere N=network code, S=station code, L=location code, C=channel code')
    prefs.add_argument('--sigfigs', required=False, help='number of significant figures used for output columns named "value"')
    prefs.add_argument('--sds_files',action='store_true',default=False,help='if set, ISPAQ will look for local data files with Seiscomp SDS naming format \nNET.STA.LOC.CHAN.TYPE.YEAR.DAY where TYPE=D')
   
    other = parser.add_argument_group('other arguments')
    other.add_argument('--log-level', action='store', default='INFO',
                        choices=['DEBUG','INFO','WARNING','ERROR','CRITICAL'],
                        help='log level printed to console, default="INFO"')
    parser.add_argument('-A', '--append', action='store_true', default=False,
                        help='append to TRANSCRIPT file rather than overwriting')
    parser.add_argument('-V', '--version', action='version',
                        version='%(prog)s ' + __version__)
    parser.add_argument('-I', '--install-r',action='store_true', default=False,
                        help='install CRAN IRIS Mustang packages, and exit')
    parser.add_argument('-U', '--update-r', action='store_true', default=False,
                        help='check for and install newer CRAN IRIS Mustang packages \nand/or update required conda packages, and exit')
    parser.add_argument('-L', '--list-metrics', action='store_true', default=False,
                        help='list names of available metrics and exit')

    try:
        args = parser.parse_args(sys.argv[1:])
    except IOError as msg:
        print(str(msg))
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

    logger.info('Running ISPAQ version %s on %s' % (__version__, datetime.datetime.now().strftime('%c')))

    # check that IRIS CRAN packages are installed

    import obspy
    from distutils.version import StrictVersion
    from . import updater 
    import rpy2.robjects as ro
    from rpy2 import rinterface 
    from rpy2.robjects import pandas2ri
    from rpy2.robjects.packages import importr
    from rpy2.robjects.conversion import localconverter

    IRIS_packages = ['seismicRoll','IRISSeismic','IRISMustangMetrics']

    r_installed = ro.r("installed.packages()")

    with localconverter(ro.default_converter + pandas2ri.converter):
        installed_names = ro.conversion.rpy2py(r_installed.rownames).tolist()

    flag=0
    for package in IRIS_packages:
        if package not in installed_names:
            print("IRIS R package " + package + " is not installed")
            flag=1
    if (flag == 1):
        print("\nAttempting to install IRIS R packages from CRAN")
        updater.install_IRIS_packages_missing(IRIS_packages,logger)


    # Validate the args --------------------------------------------------------
    
    # We can't use required=True in argpase because folks should be able to type only -U
    
    if not (args.update_r or args.install_r or args.list_metrics):
        # metric sets
        if args.metrics is None:
            logger.critical('argument -M/--metrics is required to run metrics')
            raise SystemExit
            
        # stations sets
        if args.stations is None:
            logger.critical('argument -S/--stations is required to run metrics')
            raise SystemExit
    
    
    # Handle R package upgrades ------------------------------------------------

    _R_install_packages = ro.r('utils::install.packages')

    if args.install_r:
        logger.info('(Re)installing IRIS R packages from CRAN')
        updater.install_IRIS_packages(IRIS_packages,logger)
        sys.exit(0)

    if args.update_r:
        logger.info('Checking for recommended conda packages...')
        x=ro.r("packageVersion('base')")
        x_str = ".".join(map(str,np.array(x.rx(1)).flatten()))
        if ((StrictVersion(obspy.__version__) < StrictVersion("1.2.2")) 
                 or (StrictVersion(x_str) < StrictVersion("3.5.1")) ):
            logger.debug('Obspy 1.2.2 not found')
            logger.info('Updating conda packages...')
            conda_str = ("conda update -c conda-forge pandas=1.2.3 obspy=1.2.2 r=3.6 " +
                    " r-rcurl=1.98_1.3 r-xml=3.99_0.3 r-dplyr=1.0.6 r-quadprog=1.5_8 r-signal=0.7_6" +
                    " r-pracma=2.3.3 rpy2=3.1.0 r-stringr=1.4.0")
            subprocess.call(conda_str, shell=True)
            logger.info('(Re)installing IRIS R packages from CRAN')
            try:
                for package in IRIS_packages:
                    _R_install_packages(package)
                    logger.info('Installed %s' % (package))
            except Exception as e:
                logger.error('Unable to install %s: %s' % (package,e))
        else:
            logger.info('Required conda packages found')

        logger.info('Checking for IRIS R package updates...')
        df = updater.get_IRIS_package_versions(IRIS_packages,logger)
        print('\n%s\n' % df)
        updater.update_IRIS_packages(IRIS_packages,logger)
        sys.exit(0)

    if args.list_metrics:
        logger.info('Checking for available metrics in IRIS R packages...')
        from . import irismustangmetrics
        default_function_dict = irismustangmetrics.function_metadata()
        ispaq_dict = currentispaq()
        metricList = []
        for function_name in default_function_dict:
            default_function = default_function_dict[function_name]
            bLogic = default_function['businessLogic']
            for metric_name in default_function['metrics']:
                if metric_name not in ['pdf_plot','pdf_text']:
                    if bLogic not in ispaq_dict:    
                        metricList.append(metric_name + "  *metric will not run with this version of ISPAQ*")
                    else:
                        if function_name not in ispaq_dict[bLogic]:
                            metricList.append(metric_name + "  *metric will not run with this version of ISPAQ*")
                        else:
                            metricList.append(metric_name)
        for line in sorted(metricList):
            print(line)
        sys.exit(0)


    # Load additional modules --------------------------------------------------

    # These are loaded here so that asking for --version or --help is not bogged down
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
    from .sampleRate_metrics import sampleRate_metrics

    if (StrictVersion(obspy.__version__) < StrictVersion("1.2.2")):
        print("Please update ObsPy version " + str(obspy.__version__) + " to version 1.2.2")
        message = "Would you like to update obspy now? [y]/n: "
        answer = raw_input(message).lower()
        accepted_answer = ['','yes','y']
        rejected_answer = ['n','no']
        while ((answer not in accepted_answer) and (answer not in rejected_answer)):
            print("Invalid choice: " + answer)
            message = "Would you like to update obspy now? [y]/n: "
            answer = raw_input(message).lower()
        if answer in accepted_answer:
            subprocess.call("conda install -c conda-forge obspy=1.2.2",shell=True)
        elif answer in rejected_answer:
            print("Exiting now without updating conda packages.")
            raise SystemExit


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
                    if concierge.output == 'csv':
                        logger.info('Writing simple metrics to %s' % filepath)
                    elif concierge.output == 'db':
                        logger.info('Writing simple metrics to %s' % concierge.db_name)
                    utils.write_simple_df(df, filepath, concierge, sigfigs=concierge.sigfigs)
                except Exception as e:
                    logger.debug(e)
                    logger.error("Error writing 'simple' metric results")
        except NoAvailableDataError as e:
            logger.info("No data available for 'simple' metrics")
        except Exception as e:
            logger.debug(e)
            logger.error("Error calculating 'simple' metrics")

    
    if 'sampleRate' in concierge.logic_types:
        logger.debug('Inside sampleRate business logic ...')
        try:
            df = sampleRate_metrics(concierge)
            if df is None:
                logger.info('No sampleRate metrics were calculated')
            else:
                try:
                    filepath = concierge.output_file_base + "_sampleRateMetrics.csv"
                    if concierge.output == 'csv':
                        logger.info('Writing sampleRate metrics to %s' % filepath)
                    elif concierge.output == 'db':
                        logger.info('Writing sampleRate metrics to %s' % concierge.db_name)
                    utils.write_simple_df(df, filepath, concierge, sigfigs=concierge.sigfigs)
                except Exception as e:
                    logger.debug(e)
                    logger.error("Error writing 'sampleRate' metric results")
        except NoAvailableDataError as e:
            logger.info("No data available for 'sampleRate' metrics")
        except Exception as e:
            logger.debug(e)
            logger.error("Error calculating 'sampleRate' metrics")

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
                    
                    if concierge.output == 'csv':
                        logger.info('Writing SNR metrics to %s' % filepath)
                    elif concierge.output == 'db':
                        logger.info('Writing SNR metrics to %s' % concierge.db_name)
                    utils.write_simple_df(df, filepath, concierge, sigfigs=concierge.sigfigs)
                except Exception as e:
                    logger.debug(e)
                    logger.error("Error writing 'SNR' metric results")
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
            if 'PSD' not in concierge.function_by_logic['PSD']:
                pass
            elif df is None:
                logger.info('No PSD metrics were calculated')
            else:
                try:
                    # Write out the metrics
                    filepath = concierge.output_file_base + "_PSDMetrics.csv"
                    if concierge.output == 'csv':
                        logger.info('Writing PSD metrics to %s' % filepath)
                    elif concierge.output == 'db':
                        logger.info('Writing PSD metrics to %s' % concierge.db_name)
                    utils.write_simple_df(df, filepath, concierge, sigfigs=concierge.sigfigs)
                except Exception as e:
                    logger.debug(e)
                    logger.error("Error writing 'PSD' metric results")
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
                logger.info('No crossTalk metrics were calculated')
            else:
                try:
                    filepath = concierge.output_file_base + "_crossTalkMetrics.csv"
                    if concierge.output == 'csv':
                        logger.info('Writing crossTalk metrics to %s' % filepath)
                    elif concierge.output == 'db':
                        logger.info('Writing crossTalk metrics to %s' % concierge.db_name)
                    utils.write_simple_df(df, filepath, concierge, sigfigs=concierge.sigfigs)
                except Exception as e:
                    logger.debug(e)
                    logger.error("Error writing 'crossTalk' metric results")
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
                    if concierge.output == 'csv':
                        logger.info('Writing pressureCorrelation metrics to %s' % filepath)
                    elif concierge.output == 'db':
                        logger.info('Writing pressureCorrelation metrics to %s' % concierge.db_name)
                    utils.write_simple_df(df, filepath, concierge, sigfigs=concierge.sigfigs)
                except Exception as e:
                    logger.debug(e)
                    logger.error("Error writing 'pressureCorrelation' metric results")
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
                    if concierge.output == 'csv':
                        logger.info('Writing crossCorrelation metrics to %s' % filepath)
                    elif concierge.output == 'db':
                        logger.info('Writing crossCorrelation metrics to %s' % concierge.db_name)
                    utils.write_simple_df(df, filepath, concierge, sigfigs=concierge.sigfigs)
                except Exception as e:
                    logger.debug(e)
                    logger.error("Error writing 'crossCorrelation' metric results")
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
                    if concierge.output == 'csv':
                        logger.info('Writing orientationCheck metrics to %s' % filepath)
                    elif concierge.output == 'db':
                        logger.info('Writing orientationCheck metrics to %s' % concierge.db_name)
                    utils.write_simple_df(df, filepath, concierge, sigfigs=concierge.sigfigs)
                except Exception as e:
                    logger.debug(e)
                    logger.error("Error writing 'orientationCheck' metric results")
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
                    if concierge.output == 'csv':
                        logger.info('Writing transfer metrics to %s' % filepath)
                    elif concierge.output == 'db':
                        logger.info('Writing transferFunction metrics to %s' % concierge.db_name)
                    utils.write_simple_df(df, filepath, concierge, sigfigs=concierge.sigfigs)
                except Exception as e:
                    logger.debug(e)
                    logger.error("Error writing 'transferFunction' metric results")
        except NoAvailableDataError as e:
            logger.info("No data available for 'transferFunction' metrics")
        except Exception as e:
            logger.debug(e)
            logger.error("Error calculating 'transferFunction' metrics")


    logger.info('ALL FINISHED!')


# ------------------------------------------------------------------------------

if __name__ == "__main__":
    main()
