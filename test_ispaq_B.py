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

import ispaq.utils.metric_sets as metric_sets
import ispaq.utils.sncls as sncl_utils
import ispaq.utils.preferences as preferences
from ispaq.utils.misc import *

from ispaq.concierge import Concierge, DummyUserRequest

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
    #
    # The user_request class is in charge of parsing arguments, loading and
    # parsing a preferences file and setting a bunch of properties that capture
    # the totality of what the user wants in this invocation of the script.
    #
    # Properties that must be specified include at a minimum:
    #  * metric_names[]
    #  * sncl_patterns[]
    #  * starttime
    #  * endtime
    #  * event_url
    #  * station_url
    #  * dataselect_url
    #
    # All methods are internal except for load_json() and dump_json() which can
    # be used for debugging. The user_request will be stored by the concierge
    # for future reference.
    #
    # Think of the methods of the user_request object as the work of a lower
    # level front desk person who is taking guest information from a handwritten
    # request (preferences file) and phone call (command line arguments)
    # and transcribing that info[ onto a standard form that the cocierge keeps
    # for each guest. (Each unique invocation of this script is a new 'guest'.)
    # 
    # When the guest asks for something later, the concierge has already done
    # the background work and can provide the guest whatever they want in their
    # preferred format.

    #try:
        #user_request = ispaq.user_request(args)
    #except userRquestError:
        #print(user_requestError)

    user_request = DummyUserRequest()

    # Create Concierge (aka Expediter) -----------------------------------------
    #
    # The concierge uses the completely filled out user_request and has the
    # job of expediting requests for information that may be made by any of the
    # business_logic methods.
    #
    # The goal is to have business_logic methods that can be written as clearly
    # as possible without having to know about the intricacies of ObsPy. Thus,
    # if business logic needs a list of SNCLs, they should be able to say:
    #
    #   concierge.get_sncl_list()
    #
    # If they would rather work with an ObsPy Inventory, then:
    #
    #   concierge.get_sncl_inventory()
    #
    # It is assumed that all of the information required to generate this list 
    # or inventory of sncls [starttime, endtime, sncl_patterns, client_url, ...]
    # are part of the user_request object that the concierge has access to
  
    try:
        concierge = Concierge(user_request)
    except Exception as e:
        if str(e) == "Not really an error.":
            pass
        else:
            raise

    # dummy test
    print(concierge.get_sncls())


    # Generate Simple Metrics --------------------------------------------------

    #try:
      #simple_output = ispaq.business_logic.generate_simple_metrics(concierge)
      #try:
          ## Dump output to a file
      #except:
          ##
    #except:
          ##


    # Generate SNR Metrics -----------------------------------------------------

    #try:
      #snr_output = ispaq.business_logic.generate_SNR_metrics(concierge)
      #try:
          ## Dump output to a file
      #except:
          ##
    #except:
          ##


    # Generate [increasingly complex/time-consuming metrics] -------------------

    #try:
      #complex_output = ispaq.business_logic.generate_complex_metrics(concierge)
      #try:
          ## Dump output to a file
      #except:
          ##
    #except:
          ##
    
        
    # Cleanup ------------------------------------------------------------------

if __name__ == "__main__":
    main()
