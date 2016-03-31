#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Initial stab at ISPAQ script.

This version runs from command line arguments only and assumes that we are 
connected to the internet.
"""
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
from future.builtins import *  # NOQA

import argparse

from ispaq.irismustangmetrics import *

import ispaq.utils.metric_calculators as metric_sets
import ispaq.utils.sncls as sncl_utils
from ispaq.concierge.user_requests import UserRequest
from ispaq.utils.misc import *

import pandas as pd

import sys

from os.path import expanduser

import obspy

__version__ = "0.0.1"


def main(argv=None):
    
    # Parse arguments ----------------------------------------------------------
    
    parser = argparse.ArgumentParser(description=__doc__.strip())
    parser.add_argument('-V', '--version', action='version',
                        version='%(prog)s ' + __version__)
    parser.add_argument('--example-data', action='store_true', default=False,
                        help='use example data from local disk')
    parser.add_argument('--sncl', action='store', default=None,
                        help='Network.Station.Location.Channel identifier (e.g. US.OXF..BHZ)')
    parser.add_argument('--start', action='store', default=None,
                        help='starttime in ISO 8601 format')
    parser.add_argument('--end', action='store', default=None,
                        help='starttime in ISO 8601 format')
    parser.add_argument('-M', '--metric-set-name', required=True,
                        help='name of metric to calculate')  # TODO re-add the limit
    parser.add_argument('-P', '--preference-file', default=expanduser('~/.irispref'),
                        type=argparse.FileType('r'), help='location of preference file')
    parser.add_argument('-O', '--output-loc', default='.',
                        help='location to output ')
    parser.add_argument('-S', '--sigfigs', type=check_negative, default=6,
                        help='number of significant figures to round metrics to')

    args = parser.parse_args(argv)

    if not args.example_data and (not args.sncl or not args.start):
        sys.exit('Requires either --example data or --start and --sncl')

    # Load Preferences ---------------------------------------------------------
    
    user_request = UserRequest(args.start, args.end, args.metric_set_name, args.sncl, args.preference_file)
    print(user_request)

    # TODO: validate and or build sncls
    # TODO: Verify that desired metric set exists in preference file or otherwise

    # Obtain data --------------------------------------------------------------
    
    if args.example_data:
        # Obtain data from file on disk
        from ispaq.irisseismic import R_Stream
        import os
        filepath = os.path.abspath('./test.mseed')
        stream = obspy.read(filepath)
        r_streams = pd.Series(R_Stream(stream))
        args.start = 'example'
    else:
        # Obtain data from IRIS DMC
        from ispaq.irisseismic import R_getSNCL
        from rpy2.rinterface import RRuntimeError

        sncls = sncl_utils.get_simple_sncls(user_request)

        print('Building %s Streams' % len(sncls))
        try:  # in case lack of internet
            r_streams = sncls.apply(lambda sncl: statuswrap(R_getSNCL, 0, RRuntimeError, sncl,
                                                            user_request.requested_start_time,
                                                            user_request.requested_end_time))
            r_streams = r_streams.dropna()
        except RRuntimeError:
            sys.exit('\033[91m\nError: Could not fetch data. '
                     'Check your internet connection?\033[0m\n')
        print('Building streams complete.\n')

    # Calculate the metric and save the result ---------------------------------
    
    # TODO:  Need a dictionary so we can test whether a metrics is "simple" or something else.
    
    # TODO:  Future iterations will need to handle the possibility that a metric alias
    # TODO:  will refer to simple and other types of metrics. In these cases it may be necessary
    # TODO:  to deal with all of the simple metrics in a block first, outputting one csv file
    # TODO:  for them and then continuing with other categories of metrics whose data will
    # TODO:  will be stored in other files.
    
    if True:
        df = metric_sets.simple_set(args.metric_set_name, user_request.required_metric_set_functions, r_streams, sigfigs=args.sigfigs)
        if df is not None:
            file_name = args.metric_set_name + '_' + args.start + '.csv'
            path = args.output_loc + '/' + file_name
            df.to_csv(path, index=False)
            
            print(('=' * 34) + ' OUTPUT ' + ('=' * 34))
            print(df)
    else:
        # TODO: Need to figure out what to do with non-"simple" metrics.
        print('This will output something eventually')
        

if __name__ == "__main__":
    main()
