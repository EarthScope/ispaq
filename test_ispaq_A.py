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

from obspy.core import UTCDateTime
from obspy.fdsn import Client

import pandas as pd

from ispaq.irismustangmetrics import listMetricFunctions, applyMetric

__version__ = "0.0.1"


def main(argv=None):
    from ispaq.irismustangmetrics import simpleMetricsOutput as smo
    
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
    parser.add_argument('--end', action='store', required=True,
                        help='endtime in ISO 8601 format')
    parser.add_argument('--metric-name', choices=listMetricFunctions(),
                        help='name of metric to calculate')

    args = parser.parse_args(argv)

    
    # Validate arguments -------------------------------------------------------
    
    sncl = args.sncl
    starttime = UTCDateTime(args.start) # Test date for US.OXF..BHZ is 2002-04-20 + 1 day
    endtime = UTCDateTime(args.end)
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
        
        
    # Calculate the metric and print the result --------------------------------
    
    df = applyMetric(r_stream,metricName)
    print(df)
    smo(df, '~/Projects/ISPAQ/output.csv')
    

if __name__ == "__main__":
    main()
