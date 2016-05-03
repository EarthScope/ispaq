# -*- coding: utf-8 -*-


"""ispaq.ispaq: provides entry point main()."""


__version__ = "0.4.1"


import sys
import os
import argparse

from concierge import Concierge
from user_request import UserRequest
import irisseismic
import irismustangmetrics
import utils

from simple_metrics import simple_metrics
from SNR_metrics import SNR_metrics

def main():
    ###print("Executing ispaq version %s." % __version__)
    ###print("List of argument strings: %s" % sys.argv[1:])

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
    parser.add_argument('--verbose', action='store_true', default=False,
                        help='print out detailed progress information')

    # TODO:  additional configurable elements like sigfigs should be in the preferences file
    # parser.add_argument('--sigfigs', type=check_negative, default=6,
    #                     help='number of significant figures to round metrics to')

    args = parser.parse_args(sys.argv[1:])
    
    print(args)


    #     Create UserRequest object     ---------------------------------------
    #
    # The UserRequest class is in charge of parsing arguments issued on the
    # command line, loading and parsing a preferences file, and setting a bunch
    # of properties that capture the totality of what the user wants in a single
    # invocation of the ISPAQ top level script.

    try:
        user_request = UserRequest(args, verbose=args.verbose)
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
  
    try:
        concierge = Concierge(user_request, verbose=args.verbose)
    except Exception as e:
        if str(e) == "Not really an error.":
            pass
        else:
            raise


    #     Generate Simple Metrics     ------------------------------------------

    if 'simple' in concierge.logic_types:
        try:
            simple_df = simple_metrics(concierge, verbose=args.verbose)
            try:
                filename = concierge.output_file_base + "__simpleMetrics.csv"
                print('\nWriting simple metrics to %s.\n' % filename)
                simple_df = utils.format_simple_df(simple_df, sigfigs=6)
                simple_df.to_csv(filename)
            except Exception as e:
                print('Exception to dump to a file: %s' % e)
        except Exception as e:
            print(str(e))


    # Generate SNR Metrics -----------------------------------------------------

    if 'SNR' in concierge.logic_types:
        try:
            SNR_df = SNR_metrics(concierge, verbose=True)
            try:
                filename = concierge.output_file_base + "__SNRMetrics.csv"
                print('\nWriting SNR metrics to %s.\n' % filename)
                SNR_df = utils.format_simple_df(SNR_df, sigfigs=6)
                SNR_df.to_csv(filename)
            except Exception as e:
                print('Exception to dump to a file: %s' % e)
        except Exception as e:
            print(str(e))


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
#    
#        
#    # Cleanup ------------------------------------------------------------------
#
#if __name__ == "__main__":
#    main()
