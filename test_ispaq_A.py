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

import ispaq.utils.metric_sets as ms
from ispaq.utils.misc import *

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
    parser.add_argument('-M', '--metric-set-name',
                        help='name of metric to calculate')  # TODO re-add the limit
    parser.add_argument('-P', '--preference-file', default='~/.irispref',
                        help='location of preference file')
    parser.add_argument('-O', '--output-loc', default='.',
                        help='location to output ')

    args = parser.parse_args(argv)
    
    # Load Preferences ---------------------------------------------------------
    
    custom_metric_sets, custom_sncls = preferenceloader(args.preference_file)
    function_sets, custom_metric_errs = ms.validate(custom_metric_sets)
            
    # Format arguments ---------------------------------------------------------
    
    sncl = args.sncl
    starttime = UTCDateTime(args.start)  # Test date for US.OXF..BHZ is 2002-04-20 + 1 day
    endtime = starttime + (24 * 3600)
        
    # Obtain data --------------------------------------------------------------
    
    if args.example_data:
        # Obtain data from file on disk
        from obspy import read
        from ispaq.irisseismic import R_Stream
        import os
        filepath = os.path.abspath('./test.mseed')
        stream = read(filepath)
        r_stream = R_Stream(stream)        
    else:
        # Obtain data from IRIS DMC
        from ispaq.irisseismic import R_getSNCL
        r_stream = R_getSNCL(sncl, starttime, endtime)

    # Calculate the metric and save the result ---------------------------------
    
    # TODO:  Need a dictionary so we can test whether a metrics is "simple" or something else.
    
    # TODO:  Future iterations will need to handle the possibility that a metric alias
    # TODO:  will refer to simple and other types of metrics. In these cases it may be necessary
    # TODO:  to deal with all of the simple metrics in a block first, outputting one csv file
    # TODO:  for them and then continuing with other categories of metrics whose data will
    # TODO:  will be stored in other files.
    
    if True:
        df = ms.simpleset(args.metric_set_name, function_sets, r_stream)
        file_name = args.metric_set_name + '_' + args.start + '.csv'
        path = args.output_loc + '/' + file_name
        df.to_csv(path, index=False)        
    else:
        # TODO: Need to figure out what to do with non-"simple" metrics.
        print('This will output something eventually')
        

if __name__ == "__main__":
    main()
