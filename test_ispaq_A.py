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


def preferenceLoader(pref_loc):
    """
    Safely loads preference file from the specified location
    :param pref_loc: string file location
    :return: a tuple (metrics, sncls) where each refers to the specified
             sub-dictionary of the JSON file
    """
    try: # check if file exists
        from os.path import expanduser
        pref_loc = expanduser(pref_loc)
        pref_file = open(pref_loc, 'r')
        print('Loading preferences from %s...' %pref_loc)
        preferences = json.load(pref_file)        
    except AttributeError:
        print(sys.exc_info())
        print('No user preferences discovered. Ignoring...\n')
        return None
    
    try: # check if file contains custom metrics
        print('   Custom metric sets...', end='\t')
        custom_metric_sets = preferences['MetricAlias']
        print('Done')
    except KeyError:
        custom_metric_sets = None
        print('not found')
        
    try: # check if file contains custom sncls
        print('   Custom SNCLs...', end='\t')
        custom_sncl = preferences['SNCLAlias']        
        print('Done')
    except KeyError:
        custom_sncl = None
        print('Not found')
        
    print('Preferences loaded.\n')    
    return (custom_metric_sets, custom_sncl)


def validateCustomMetricSets(metric_functions, custom_metricsets):
    """Validates custom metric sets and returns the necesary metric
    functions and an error list"""
    
    print('Validating custom metrics...')
    error_list = []
    custom_metricset_functions = {}
    
    # Creates a dictionary of {needed functions: [list of needed metrics that they provide]}
    for custom_metricset in custom_metricsets:
        required_functions = {}
        for metric in custom_metricsets[custom_metricset]:
            try: # check if metric exists
                function = metric_functions[metric]
            except KeyError:
                print('   Metric "%s" not found' %metric)
                error_list.append(metric)
            
            if function in required_functions:
                required_functions[function].append(metric)
            else:
                required_functions[function] = [metric]
            
        custom_metricset_functions[custom_metricset] = required_functions
    
    print('Finished validating with %d errors.\n' %len(error_list))
    return (custom_metricset_functions, error_list)
    
   
def metricsList(function_data):
    '''Returns a dictionary of {metrics: functionNames} based on the metrics and functions
    contained within the Metric Metadata'''
    
    # invert the dictionary to be {metric: functionName}
    # TODO: potentially move this to a class wrapping the original dict
    metric_functions = {}
    for function in function_data:
        for metric in function_data[function]['metrics']:
            metric_functions[metric] = function
            
    return metric_functions


def getSimpleMetricSet(r_stream, function_metadata, custom_metricset_functions, metric_set):
    '''
    Returns a dataframe with the metrics specified in the metric_set
    :param r_stream: r_stream
    :param function_metadata: the metadata of all the default metric sets
    :param custom_metricset_functions: dictionary of needed functions (see validateCustomMetricSets)
    :param metric_set: the desired set of metrics
    :returns: a dataframe with the desired metrics
    '''
    if metric_set in function_metadata: # if a preset metric-set 
        df = applySimpleMetric(r_stream, metric_set)
        # Create a pretty version of the dataframe
        df = simpleMetricsPretty(df, sigfigs=6)
        print(df)
        return df
    
    elif metric_set in custom_metricset_functions: # if a custom metric-set
        import pandas as pd
        df_peices = []
        metric_set_functions = custom_metricset_functions[metric_set]
        for function in metric_set_functions:
            tempdf = applySimpleMetric(r_stream, function)
            tempdf = tempdf.loc[tempdf['metricName'].isin(metric_set_functions[function])]
            df_peices.append(tempdf)
        df = pd.concat(df_peices)
        print(df)
        return df
    
    print('Metric Set not found')
    

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
                        help='name of metric to calculate') # TODO re-add the limit
    parser.add_argument('-P', '--preference-file', default='~/.irispref',
                        help='location of preference file')
    parser.add_argument('-O', '--output-loc', default='.',
                        help='location to output ')

    args = parser.parse_args(argv)

    # Load function data -------------------------------------------------------
    
    from ispaq.irismustangmetrics.metrics import _R_getMetricFunctionMetdata
    function_metadata = _R_getMetricFunctionMetdata()    
    
    metric_functions = metricsList(function_metadata)
    
    # Load Preferences ---------------------------------------------------------
    
    custom_metric_sets, custom_sncls = preferenceLoader(args.preference_file)
    function_sets, custom_metric_errs = validateCustomMetricSets(metric_functions, custom_metric_sets)
            
    # Format arguments ---------------------------------------------------------
    
    sncl = args.sncl
    starttime = UTCDateTime(args.start) # Test date for US.OXF..BHZ is 2002-04-20 + 1 day
    endtime = starttime + (24 * 3600)
    metricSetName = args.metric_set_name
    output_dir = args.output_loc
        
        
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
        df = getSimpleMetricSet(r_stream, function_metadata, function_sets, metricSetName)
        file_name = metricSetName + '_' + args.start + '.csv'
        path = output_dir + '/' + file_name
        df.to_csv(path, index=False)        
    else:
        print('Need to figure out what to do with non-"simple" metrics.')
        

if __name__ == "__main__":
    main()
