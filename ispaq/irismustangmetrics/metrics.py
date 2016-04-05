#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Python module containing wrappers for the IRISMustangMetrics R package.
:copyright:
    Mazama Science
:license:
    GNU Lesser General Public License, Version 3
    (http://www.gnu.org/copyleft/lesser.html)
    
Metrics from the IRISMustangMetrics package fall into several categories
depending on the following factors:

* whether special *business logic* is required to identify appropriate data
* number of r_stream objects passed in (1 or 2)
* return type (single values, multilpe values, times, spectra, *etc.*)

Functions in the IRISMustangMetrics R package provide this metadata so that
functions can be called programmatically from python without the user having
to know anything about the particular metric function they are calling.
"""
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
from future.builtins import *  # NOQA


### ----------------------------------------------------------------------------


from obspy.core import UTCDateTime

import pandas as pd

# Connect to R through the rpy2 module
from rpy2.robjects import r, pandas2ri

# R options
r('options(digits.secs=6)')      # print out fractional seconds


###   R functions called internally     ----------------------------------------


# NOTE:  These functions behave exactly the same as the R versions and require
# NOTE:  R-compatible objects as arguments.

# IRISMustangMetrics helper functions
_R_metricList2DF = r('IRISMustangMetrics::metricList2DF')
_R_metricList2Xml = r('IRISMustangMetrics::metricList2Xml')


def _R_getMetricFunctionMetdata():
    """
    This function should probably return a python dictionary with the following
    information:
     * name -- char
     * streamCount -- int, (number of streams on input)
     * fullDay -- logical
     * outputType -- char, [SingleValue | MultipleValue | MultipleTime | Spectrum | Other?]
     * speed -- char, [slow | medium | fast] (set basic expecations)
     * extraAttributes -- char, (comma separated list of extra attributes returned in DF)
     * businessLogic -- char, (Description of business logic which should be implmented in python.)
    """
    # TODO:  Replace this functionality with IRISMustangMetrics::getMetricMetadata
    functiondict = {
        'basicStats': {
            'streamCount': 1,
            'outputType': 'SingleValue',
            'fullDay': True,
            'speed': 'fast',
            'extraAttributes': None,
            'businessLogic': 'simple',
            'metrics': ['sample_min',
                        'sample_median',
                        'sample_mean',
                        'sample_max',
                        'sample_rms']
            },
        'gaps': {
            'streamCount': 1,
            'outputType': 'SingleValue',
            'fullDay': True,
            'speed': 'fast',
            'extraAttributes': None,
            'businessLogic': 'simple',
            'metrics': ['num_gaps',
                        'max_gap',
                        'num_overlaps',
                        'max_overlap',
                        'percent_availability']
            },
        'stateOfHealth': {
            'streamCount': 1,
            'outputType': 'SingleValue',
            'fullDay': True,
            'speed': 'fast',
            'extraAttributes': None,
            'businessLogic': 'simple',
            'metrics': ["calibration_signal",
                        "timing_correction",
                        "event_begin",
                        "event_end",
                        "event_in_progress",
                        "clock_locked",
                        "amplifier_saturation",
                        "digitizer_clipping",
                        "spikes",
                        "glitches",
                        "missing_padded_data",
                        "telemetry_sync_error",
                        "digital_filter_charging",
                        "suspect_time_tag",
                        "timing_quality"]
            },
        
        'STALTA': {
            'streamCount': 1,
            'outputType': 'SingleValue',
            'fullDay': True,
            'speed': 'slow',
            'extraAttributes': None,
            'businessLogic': 'Limit to BH and HH channels.',
            'metrics': ['max_stalta']
            },
        'spikes': {
            'streamCount': 1,
            'outputType': 'SingleValue',
            'fullDay': True,
            'speed': 'fast',
            'extraAttributes': None,
            'businessLogic': 'simple',
            'metrics': ['num_spikes']
        }
    }
    return(functiondict)

###   R functions still to be written     --------------------------------------


def function_metadata():
    return _R_getMetricFunctionMetdata()


def metricslist(function_data=_R_getMetricFunctionMetdata()):
    """
    :param function_data: the function metadata returned by _R_getMetricFunctionMetdata
    :return: a dictionary of {metrics: functionNames} based on the metrics and functions
    contained within the Metric Metadata
    """

    # invert the dictionary to be {metric: functionName}
    # TODO: potentially move this to a class wrapping the original dict
    metric_functions = {}
    for function in function_data:
        for metric in function_data[function]['metrics']:
            metric_functions[metric] = function

    return metric_functions


def listMetricFunctions(functionType="simple"):
    """
    Function to be added to the IRISMustangMetrics package.
    
    "simple" metrics are those that require only a single stream as input and
    return a metricList of SingleValueMetrics as output. They may may have
    additional arguments which can be used but the provided defaults are 
    typically adequate.

    """
    df = pd.DataFrame.from_dict(_R_getMetricFunctionMetdata(), orient='index')
    names = df.index.tolist()

    functionlist = _R_getMetricFunctionMetdata().keys()
    
    return functionlist


def simpleMetricsPretty(df, sigfigs=6):
    """
    Create a pretty dataframe with appropriate significant figures.
    :param df: Dataframe of simpleMetrics.
    :param sigfigs: Number of significant figures to use.
    :return: Dataframe of simpleMetrics.
    
    The following conversions take place:
    
    * Round the 'value' column to the specified number of significant figures.
    * Convert 'starttime' and 'endtime' to python 'date' objects.
    """
    df.value = df.value.astype(float)
    df.value = df.value.apply(lambda x: signif(x, sigfigs))
    df.starttime = df.starttime.apply(lambda x: getattr(x, 'date'))
    df.endtime = df.endtime.apply(lambda x: getattr(x, 'date'))
    return df
    
    
def signif(number, sigfigs=6):
    """
    Returns number rounded to the specified number of significant figures.
    :param number: Floating point number.
    :param sigfigs: Significant figures to use.
    :return: Number rounded to sigfigs significant figures.
                
    .. rubric:: Example
    
    >>> signif(123.456, 1)
    100.0
    >>> signif(123.456,3)
    123.0
    >>> signif(123.456,4)
    123.5
    >>> signif(123.456,7)
    123.456
    
    """
    from math import log10, floor
    digit = -int(floor(log10(abs(number)))) + (sigfigs - 1)
    if digit > 0:
        return round(number, digit)
    else: # future.builtins.newround doesn't handle negative ndigits yet (3/3/16)
        return number - (number % (10 ** -digit))

###   Functions for SingleValueMetrics     -------------------------------------


def applySimpleMetric(r_stream, metric_set_name, *args, **kwargs):
    """"
    Invoke a named "simple" R metric and convert the R dataframe result into
    a Pandas dataframe.
    :param r_stream: an r_stream object
    :param metric_set_name: the name of the set of metrics
    :return:
    """
    function = 'IRISMustangMetrics::' + metric_set_name + 'Metric'
    R_function = r(function)
    r_metriclist = R_function(r_stream, *args, **kwargs)  # args and kwargs shouldn't be needed in theory
    r_dataframe = _R_metricList2DF(r_metriclist)
    df = pandas2ri.ri2py(r_dataframe)
    
    # Applies UTCDateTime to start and end time columns
    df.starttime = df.starttime.apply(UTCDateTime)
    df.endtime = df.endtime.apply(UTCDateTime)
    return df


### ----------------------------------------------------------------------------


if __name__ == '__main__':
    import doctest
    print(doctest.testmod(exclude_empty=True))
