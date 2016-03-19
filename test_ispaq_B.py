#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Second stab at ISPAQ script.

This version runs from command line arguments only.
"""

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
from future.builtins import *  # NOQA

import argparse

from ispaq.irismustangmetrics import *

import ispaq.utils.metric_calculators as metric_sets
import ispaq.utils.sncls as sncl_utils
import ispaq.utils.preferences as preferences
from ispaq.utils.misc import *

import pandas as pd

import sys

from os.path import expanduser

import obspy

__version__ = "0.0.2"


def main(argv=None):
    
    # Parse arguments ----------------------------------------------------------
    
    parser = argparse.ArgumentParser(description=__doc__.strip())
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
    parser.add_argument('-P', '--preference-file', default=expanduser('~/.irispref'),
                        type=argparse.FileType('r'), help='location of preference file')
    parser.add_argument('-O', '--output-loc', default='.',
                        help='location to output ')
    parser.add_argument('-S', '--sigfigs', type=check_negative, default=6,
                        help='number of significant figures to round metrics to')

    args = parser.parse_args(argv)
    
    # Load Preferences ---------------------------------------------------------

    try:
        userRequest = ispaq.userRequest(args)
    except userRquestError:
        print(userRequestError)

    # Generate Simple Metrics -------------------------------------------------

    try:
        simple_output = ispaq.businessLogic.generateSimpleMetrics(userRequest)
        try: # Dump output to a file
            pass
        except:
            pass
    except:
        pass

    # Generate SNR Metrics ----------------------------------------------------

    try:
        snr_output = ispaq.businessLogic.generateSNRMetrics(userRequest)
        try:
            pass # Dump output to a file
        except:
            pass
    except:
        pass

    # Generate [increasingly complex/time-consuming metrics] ------------------

    try:
        complex_output = ispaq.businessLogic.generateComplexMetric(userRequest)
        try:
          pass # Dump output to a file
        except:
          pass
    except:
          pass
        
    # Cleanup -----------------------------------------------------------------

if __name__ == "__main__":
    main()
