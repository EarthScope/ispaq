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

from irisseismic import R_Stream
from irismustangmetrics import R_basicStatsMetric, R_gapsMetric

__version__ = "0.0.1"


def main(argv=None):
    # Parse arguments ----------------------------------------------------------
    parser = ArgumentParser(description=__doc__.strip())
    parser.add_argument('-V', '--version', action='version',
                        version='%(prog)s ' + __version__)
    parser.add_argument('--sncl', action='store', required=True,
                        help='Network.Station.Location.Channel identifier (e.g. US.OXF..BHZ)')
    parser.add_argument('--start', action='store', required=True,
                        help='starttime in ISO 8601 format')
    parser.add_argument('--end', action='store', required=True,
                        help='endtime in ISO 8601 format')
    parser.add_argument('--basic-stats', action='store_true',
                        help='print basic stats metrics')
    parser.add_argument('--gaps', action='store_true',
                        help='print out gap metrics')

    args = parser.parse_args(argv)

    
    # Validate arguments -------------------------------------------------------
    try:
        (network, station, location, channel) = args.sncl.split('.')
    except ValueError:
        raise ValueError('The sncl argument must contain exactly 3 "." separators.')
    starttime = UTCDateTime(args.start) # default to 2002-04-20 + 1 day
    endtime = UTCDateTime(args.end)
        
    
    
    # Create a new IRIS client
    client = Client("IRIS")
    stream = client.get_waveforms('US', 'OXF', '', 'BHZ', starttime, endtime)
    
    r_stream = R_Stream(stream, starttime, endtime)
     
    if args.basic_stats:
        basicStats_df = R_basicStatsMetric(r_stream)
        print(basicStats_df)
    
    if args.gaps:
        gaps = R_gapsMetric(r_stream)
        print(gaps)
    

if __name__ == "__main__":
    main()
