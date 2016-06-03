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

from obspy.core import UTCDateTime

import numpy as np
import pandas as pd

# Connect to R through the rpy2 module
from rpy2 import robjects
from rpy2 import rinterface
from rpy2.robjects import pandas2ri

# R options
# NOTE:  The evalresp webservice requires integer seconds.
# NOTE:  digits.secs=6 breaks calls to getEvalresp and hence any of the PSD stuff
###robjects.r('options(digits.secs=6)')      # print out fractional seconds


###   R functions called internally     ----------------------------------------


# NOTE:  These functions behave exactly the same as the R versions and require
# NOTE:  R-compatible objects as arguments.

# IRISMustangMetrics helper functions
_R_metricList2DF = robjects.r('IRISMustangMetrics::metricList2DF')


def _R_getMetricFunctionMetdata():
    """
    This function returns a dictionary with the following information:
     * name -- char, (Name of R function to be run)
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
                        'sample_rms',
                        'sample_unique']
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
            'speed': 'fast',
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
            'speed': 'slow',
            'extraAttributes': None,
            'businessLogic': 'SNR',
            'metrics': ['sample_snr']
        },
        'PSD': {
            'streamCount': 1,
            'outputType': 'PSD',
            'fullDay': True,
            'speed': 'slow',
            'extraAttributes': None,
            'businessLogic': 'PSD',
            'metrics': ['pct_above_nhnm',
                        'pct_below_nlnm',
                        'dead_channel_exp',
                        'dead_channel_lin',
                        'dead_channel_gsn']
        },
        'PSDPlot': {
            'streamCount': 1,
            'outputType': 'plot',
            'fullDay': True,
            'speed': 'slow',
            'extraAttributes': None,
            'businessLogic': 'PSD',
            'metrics': ['pdf_plot']
        },
        'transferFunction': {
            'streamCount': 2,
            'outputType': 'SingleValue',
            'fullDay': True,
            'speed': 'slow',
            'extraAttributes': ['gain_ratio', 'phase_diff', 'ms_coherence'],
            'businessLogic': 'transferFunction',
            'metrics': ['transfer_function']
        },
        'crossTalk': {
            'streamCount': 2,
            'outputType': 'SingleValue',
            'fullDay': False,
            'speed': 'fast',
            'extraAttributes': [],
            'businessLogic': 'crossTalk',
            'metrics': ['cross_talk']
        },
        'pressureCorrelation': {
            'streamCount': 2,
            'outputType': 'SingleValue',
            'fullDay': False,
            'speed': 'fast',
            'extraAttributes': [],
            'businessLogic': 'pressureCorrelation',
            'metrics': ['pressure_effects']
        },
        'crossCorrelation': {
            'streamCount': 2,
            'outputType': 'SingleValue',
            'fullDay': False,
            'speed': 'slow',
            'extraAttributes': [],
            'businessLogic': 'crossCorrelation',
            'metrics': ['polarity_check','timing_drift']
        #},
        #'orientationCheck': {
            #'streamCount': 2,
            #'outputType': 'SingleValue',
            #'fullDay': False,
            #'speed': 'slow',
            #'extraAttributes': [],
            #'businessLogic': 'orientationCheck',
            #'metrics': ['orientation_check']
        }
    }
    return(functiondict)

def function_metadata():
    return _R_getMetricFunctionMetdata()


#     Functions that return SingleValueMetrics     -----------------------------


def apply_simple_metric(r_stream, metric_function_name, *args, **kwargs):
    """"
    Invoke a named "simple" R metric and convert the R dataframe result into
    a Pandas dataframe.
    :param r_stream: an r_stream object
    :param metric_function_name: the name of the set of metrics
    :return:
    """
    function = 'IRISMustangMetrics::' + metric_function_name + 'Metric'
    R_function = robjects.r(function)
    r_metriclist = R_function(r_stream, *args, **kwargs)  # args and kwargs shouldn't be needed in theory
    r_dataframe = _R_metricList2DF(r_metriclist)
    df = pandas2ri.ri2py(r_dataframe)
    
    # Convert columns from R POSIXct to pyton UTCDateTime
    df.starttime = df.starttime.apply(UTCDateTime)
    df.endtime = df.endtime.apply(UTCDateTime)
    return df


def apply_correlation_metric(r_stream1, r_stream2, metric_function_name, *args, **kwargs):
    """"
    Invoke a named "correlation" R metric and convert the R dataframe result into
    a Pandas dataframe.
    :param r_stream1: an r_stream object
    :param r_stream2: an r_stream object
    :param metric_function_name: the name of the set of metrics
    :return:
    """
    function = 'IRISMustangMetrics::' + metric_function_name + 'Metric'
    R_function = robjects.r(function)
    r_metriclist = R_function(r_stream1, r_stream2, *args, **kwargs)  # args and kwargs shouldn't be needed in theory
    r_dataframe = _R_metricList2DF(r_metriclist)
    df = pandas2ri.ri2py(r_dataframe)
    
    # Convert columns from R POSIXct to pyton UTCDateTime
    df.starttime = df.starttime.apply(UTCDateTime)
    df.endtime = df.endtime.apply(UTCDateTime)
    return df



#     Functions for PSDMetrics     ---------------------------------------------

def apply_PSD_metric(r_stream, *args, **kwargs):
    """"
    Invoke the PSDMetric and convert the R dataframe result into
    a Pandas dataframe.
    :param r_stream: an r_stream object
    :return:
    """
    R_function = robjects.r('IRISMustangMetrics::PSDMetric')
    r_listOfLists = R_function(r_stream, *args, **kwargs)  # args and kwargs shouldn't be needed in theory
    r_metriclist = r_listOfLists[0]
    r_dataframe = _R_metricList2DF(r_metriclist)
    df = pandas2ri.ri2py(r_dataframe)
    
    # Convert columns from R POSIXct to pyton UTCDateTime
    df.starttime = df.starttime.apply(UTCDateTime)
    df.endtime = df.endtime.apply(UTCDateTime)
    
    # TODO:  What to do about the spectra
    r_spectralist = r_listOfLists[1]
    
    return df


def apply_PSD_plot(r_stream, filepath):
    """"
    Create a PSD plot which will be written to a .png file
    opened 'png' file.
    :param r_stream: an r_stream object
    :return:
    """
    result = robjects.r('grDevices::png')(filepath)
    r_psdList = robjects.r('IRISSeismic::psdList')(r_stream)    
    result = robjects.r('IRISSeismic::psdPlot')(r_psdList, style='pdf')
    result = robjects.r('grDevices::dev.off')()

    return True



# -----------------------------------------------------------------------------


if __name__ == '__main__':
    import doctest
    print(doctest.testmod(exclude_empty=True))
