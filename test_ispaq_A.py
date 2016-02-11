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

import json

from obspy.core import UTCDateTime
from obspy.fdsn import Client

import pandas as pd

from ispaq.irismustangmetrics import *

import sys

__version__ = "0.0.1"


def main(argv=None):
    
    # Parse arguments ----------------------------------------------------------
    
    parser = ArgumentParser(description=__doc__.strip())
    parser.add_argument('-V', '--version', action='version',
                        version='%(prog)s ' + __version__)
    parser.add_argument('--example-data', action='store_true', default=False,
                        help='use example data from local disk')
    parser.add_argument('--sncl', action='store', required=True,
                        help='Network.Station.Location.Channel identifier (e.g. US.OXF..BHZ)')
    parser.add_argument('--start', action='store', required=True,
                        help='starttime in ISO 8601 format')
    parser.add_argument('--metric-name', choices=listMetricFunctions(),
                        help='name of metric to calculate')
    parser.add_argument('-P', '--preference-file', default='~/.irispref')

    args = parser.parse_args(argv)
    
    # Load Preferences ---------------------------------------------------------
    
    try:
        from os.path import expanduser
        pref_loc = expanduser(args.preference_file)
        pref_file = open(pref_loc, 'r')
        preferences = json.load(pref_file)
        print('Preferences loading from %s...' %pref_loc)
        custom_metrics = preferences['MetricAlias']
        print('Preferences loaded.\n')
    except AttributeError:
        print(sys.exc_info())
        print('No user preferences discovered. Ignoring...\n')
    except KeyError:
        print(sys.exc_info())
        print('preference file is incorrectly formated')
            
    # Validate arguments -------------------------------------------------------
    
    sncl = args.sncl
    starttime = UTCDateTime(args.start) # Test date for US.OXF..BHZ is 2002-04-20 + 1 day
    endtime = starttime + (24 * 3600)
    metricName = args.metric_name
        
        
    # Obtain data --------------------------------------------------------------
    
    if args.example_data:
        # Obtain data from file on disk
        from obspy import read
        from ispaq.irisseismic import R_Stream
        import os
        filePath = os.path.abspath('./test.mseed')
        stream = read(filePath)
        r_stream = R_Stream(stream)        
    else:
        # Obtain data from IRIS DMC
        from ispaq.irisseismic import R_getSNCL
        r_stream = R_getSNCL(sncl, starttime, endtime)
        
        
    # Calculate the metric and save the result ---------------------------------
    
    # TODO:  Need a dictionary so we can test whether a metrics is "simple" or something else.
    
    # TODO:  Future iterations will need to handle the possibilty that a metric alias
    # TODO:  will refer to simple and other types of metrics. In these cases it may be necessary
    # TODO:  to deal with all of the simple metrics in a block first, outputting one csv file
    # TODO:  for them and then continuing with other categories of metrics whose data will
    # TODO:  will be stored in other files.
    
    if True:
        df = applySimpleMetric(r_stream, metricName)
        # Create a pretty version of the dataframe
        df = simpleMetricsPretty(df, sigfigs=6)
        print(df)
        
        output_dir = '.'
        file_name = args.metric_name + '_' + args.start + '.csv'
        path = output_dir + '/' + file_name
        df.to_csv(path, index=False)
    
    else:
        print('Need to figure out what to do with non-"simple" metrics.')
        

if __name__ == "__main__":
    main()
