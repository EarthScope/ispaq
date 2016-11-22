"""
#
# test_ispaq -- test harness for ispaq -- will perform tests on a default file, unless otherwise specified
#
# run this as a package from the root ispaq directory:
# python -m ispaq.scripts.test_ispaq <options>
# options:    -P <preference_file>
#             --starttime <YYYY-MM-DD>
#             --endtime <YYYY-MM-DD>
#             --log-level <INFO,DEBUG,WARN> 
#
# example call, showing the defaults:
# python -m ispaq.scripts.test_ispaq -P ./preference_files/testprefs.txt --starttime=2016-04-20 --endtime=2016-04-21 --log-level=DEBUG
#
"""
__version__ = "TEST_2016.11.21"
import sys
import os
import time
import glob
import argparse
import logging
from ispaq.user_request import UserRequest

## for elegant SIGTERM handling
import signal
def signal_term_handler(signal, frame):
    print 'got SIGTERM...exit.'
    sys.exit(0)
    signal.signal(signal.SIGTERM, signal_term_handler) 
    
    
def main(): 
    print("Executing TEST of ISPAQ, version %s." % __version__)
    # Parse arguments ----------------------------------------------------------
    # make sure the metric and sncl names match up to the default test preferences file contents
    parser = argparse.ArgumentParser()
    parser.add_argument('--starttime', action='store', default='2016-04-20',
                        help='starttime in ISO 8601 format')
    parser.add_argument('--endtime', action='store', default='2016-04-21',
                        help='endtime in ISO 8601 format')
    parser.add_argument('-P', '--preferences-file', default=os.path.expanduser('./preference_files/testprefs.txt'),
                        type=argparse.FileType('r'), help='location of preference file')
    parser.add_argument('-O', '--output-loc', default='.',
                        help='location to output ')
    parser.add_argument('--log-level', action='store', default='DEBUG',
                        help='{DEBUG,INFO,WARNING,ERROR,CRITICAL}')
    args = parser.parse_args(sys.argv[1:])
    args.metrics = "LOAD_PREFS_ONLY"  # trigger keyword
    args.sncls = "TEST"    # dummy value
    print(args)
    
    # Set up logger for this test component -- separate from ISPAQ instances
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    ch = logging.StreamHandler()
    ch.setLevel(getattr(logging, args.log_level))
    ch.setFormatter(formatter) 
    logger.addHandler(ch)
   
    # Process the preferences file ----------------------------------------------
    logger.info("Processing preferences file...") 
    user_request = UserRequest(args, logger=logger) 
   
    # Set up test output directories ----------------------------------------------
    test_dir_root = os.path.join(args.output_loc,"TEST_ISPAQ")
    test_dir_timepath = os.path.join(test_dir_root,time.strftime('%Y%j_%H%M%S'))  # this is time-indexed for this run
    logger.info("Set up test directory: %s..." % test_dir_timepath) 
    if not os.path.exists(test_dir_timepath):
        os.makedirs(test_dir_timepath)
     
    # Set up combinations of arguments and execute each ------------------------
    logger.info("Cycle through test options...")
    for m in user_request.metric_sets.keys():
        for s in user_request.sncl_sets.keys():
            # call regular ispaq with each combination
            command = 'python -m ispaq --starttime={0} --endtime={1} --metrics={2} --sncls={3} --preferences-file={4} --log-level={5} --output-loc={6}'\
                .format(args.starttime, args.endtime, m, s, args.preferences_file.name, args.log_level, test_dir_root)
            logger.info("Preparing test run %s" % command)
            os.system(command)
    
            logger.info("Completed with test run, moving output files to time indexed directory...")        
            # move all csv and png files to the time-indexed subdirectory
            for csv_path in glob.glob(os.path.join(test_dir_root,"*.csv")):
                csv_file = os.path.basename(csv_path)
                os.rename(csv_path,os.path.join(test_dir_timepath,csv_file))
                
            for png_path in glob.glob(os.path.join(test_dir_root,"*.png")):
                png_file = os.path.basename(png_path)
                os.rename(png_path,os.path.join(test_dir_timepath,png_file))

            logger.info("End of cycle.")
            
    # Done
    logger.info("All testing completed.  Output in %s" % test_dir_timepath)

if __name__ == "__main__":
    main()