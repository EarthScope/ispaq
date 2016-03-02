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

from argparse import ArgumentParser

from ispaq.irismustangmetrics import *

import ispaq.utils.metric_sets as metric_sets
import ispaq.utils.sncls as sncl_utils
import ispaq.utils.preferences as preferences
from ispaq.utils.misc import *

import pandas as pd

import sys

import obspy

__version__ = "0.0.1"


def main(argv=None):
    
    # Parse arguments ----------------------------------------------------------
    
    parser = ArgumentParser(description=__doc__.strip())
    parser.add_argument('-V', '--version', action='version',
                        version='%(prog)s ' + __version__)
    parser.add_argument('--example-data', action='store_true', default=False,
                        help='use example data from local disk')
    parser.add_argument('--sncl', action='store', default=False,
                        help='Network.Station.Location.Channel identifier (e.g. US.OXF..BHZ)')
    parser.add_argument('--start', action='store', default=False,
                        help='starttime in ISO 8601 format')
    parser.add_argument('-M', '--metric-set-name', required=True,
                        help='name of metric to calculate')  # TODO re-add the limit
    parser.add_argument('-P', '--preference-file', default='~/.irispref',
                        help='location of preference file')
    parser.add_argument('-O', '--output-loc', default='.',
                        help='location to output ')
    parser.add_argument('-S', '--sigfigs', default=6,
                        help='number of significant figures to round metrics to')

    args = parser.parse_args(argv)
    
    if not args.example_data and (not args.sncl or not args.start):
        sys.exit('Requires either --example data or --start and --sncl')
    
    # Load Preferences ---------------------------------------------------------
    
    custom_metric_sets, custom_sncls = preferences.load(args.preference_file)
    function_sets, custom_metric_errs = metric_sets.validate(custom_metric_sets)

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
        
        # format arguments
        starttime = obspy.UTCDateTime(args.start)  # Test date for US.OXF..BHZ is 2002-04-20 + 1 day
        endtime = starttime + (24 * 3600)
        sncls = sncl_utils.get_simple_sncls(args.sncl, custom_sncls, starttime, endtime)
        
        print('Building %s Streams' % len(sncls))
        try:  # in case lack of internet
            r_streams = sncls.apply(lambda sncl: statuswrap(R_getSNCL, 0, RRuntimeError, sncl,
                                                            starttime, endtime))
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
        df = metric_sets.simple_set(args.metric_set_name, function_sets, r_streams)
        if df is not None:
            file_name = args.metric_set_name + '_' + args.start + '.csv'
            path = args.output_loc + '/' + file_name
            df.to_csv(path, index=False)
            
            print(('=' * 30) + ' OUTPUT ' + ('=' * 30))
            print(df)
    else:
        # TODO: Need to figure out what to do with non-"simple" metrics.
        print('This will output something eventually')
        

if __name__ == "__main__":
    main()
