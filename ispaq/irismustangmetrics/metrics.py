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
    This function returns a dictionary with the following information:
     * name -- char
     * streamCount -- int, (number of streams on input)
     * outputType -- char, [SingleValue | MultipleValue | MultipleTime | Spectrum | Other?]
     * fullDay -- logical
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
            'businessLogic': 'simple',
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
        },
        'SNR': {
            'streamCount': 1,
            'outputType': 'SingleValue',
            'fullDay': False,
            'speed': 'fast',
            'extraAttributes': None,
            'businessLogic': 'SNR',
            'metrics': ['sample_snr']
        }
    }
    return(functiondict)

def function_metadata():
    return _R_getMetricFunctionMetdata()


#     R functions still to be written     -------------------------------------


# TODO:  rename "simpleMetricPretty" to "single_value_metrics_pretty"
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
    format_string = "." + str(sigfigs) + "g"
    df.value = df.value.astype(float)
    df.value = df.value.apply(lambda x: format(x, format_string))
    df.starttime = df.starttime.apply(lambda x: getattr(x, 'date'))
    df.endtime = df.endtime.apply(lambda x: getattr(x, 'date'))

    return df
    
    
#     Functions for SingleValueMetrics     ------------------------------------


# TODO:  rename "apply_simple_metric" to "apply_single_value_metric"
def apply_simple_metric(r_stream, metric_function_name, *args, **kwargs):
    """"
    Invoke a named "simple" R metric and convert the R dataframe result into
    a Pandas dataframe.
    :param r_stream: an r_stream object
    :param metric_function_name: the name of the set of metrics
    :return:
    """
    function = 'IRISMustangMetrics::' + metric_function_name + 'Metric'
    R_function = r(function)
    r_metriclist = R_function(r_stream, *args, **kwargs)  # args and kwargs shouldn't be needed in theory
    r_dataframe = _R_metricList2DF(r_metriclist)
    df = pandas2ri.ri2py(r_dataframe)
    
    # Applies UTCDateTime to start and end time columns
    df.starttime = df.starttime.apply(UTCDateTime)
    df.endtime = df.endtime.apply(UTCDateTime)
    return df


# -----------------------------------------------------------------------------


if __name__ == '__main__':
    import doctest
    print(doctest.testmod(exclude_empty=True))
