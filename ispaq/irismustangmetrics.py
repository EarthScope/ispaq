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

from __future__ import (absolute_import, division, print_function)

import math
import numpy as np
import pandas as pd
import json

from obspy.core import UTCDateTime

from rpy2 import robjects
from rpy2 import rinterface
from rpy2.robjects import pandas2ri


#   R functions called internally     ------------------------------------------


# NOTE:  These functions behave exactly the same as the R versions and require
# NOTE:  R-compatible objects as arguments.

# IRISMustangMetrics helper functions
_R_metricList2DF = robjects.r('IRISMustangMetrics::metricList2DF')
_R_getMetricFunctionMetadata = robjects.r('IRISMustangMetrics::getMetricFunctionMetadata')

def function_metadata():
    r_json = _R_getMetricFunctionMetadata()
    py_json = r_json[0]
    functionMetadata = json.loads(py_json)
    return functionMetadata

#     Functions that return GeneralValueMetrics     -----------------------------


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
    
    # Convert columns from R POSIXct to python UTCDateTime
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
    pandas2ri.activate()
    r_metriclist = R_function(r_stream1, r_stream2, *args, **kwargs)  # args and kwargs shouldn't be needed in theory
    pandas2ri.deactivate()
    r_dataframe = _R_metricList2DF(r_metriclist)
    df = pandas2ri.ri2py_dataframe(r_dataframe)
    
    # Convert columns from R POSIXct to pyton UTCDateTime
    df.starttime = df.starttime.apply(UTCDateTime)
    df.endtime = df.endtime.apply(UTCDateTime)
    return df


def apply_transferFunction_metric(r_stream1, r_stream2, evalresp1, evalresp2):
    """"
    Invoke a named "correlation" R metric and convert the R dataframe result into
    a Pandas dataframe.
    :param r_stream1: an r_stream object
    :param r_stream2: an r_stream object
    :param evalresp1: pandas DataFrame of evalresp FAP for r_stream1
    :param evalresp2: pandas DataFrame of evalresp FAP for r_stream2
    :return:
    """
    R_function = robjects.r('IRISMustangMetrics::transferFunctionMetric')
    pandas2ri.activate()
   
    r_evalresp1 = pandas2ri.py2ri_pandasdataframe(evalresp1)
    r_evalresp2 = pandas2ri.py2ri_pandasdataframe(evalresp2)
    
    # Calculate the metric
    r_metriclist = R_function(r_stream1, r_stream2, r_evalresp1, r_evalresp2)
    r_dataframe = _R_metricList2DF(r_metriclist)
    df = pandas2ri.ri2py_dataframe(r_dataframe)
    
    pandas2ri.deactivate()
    
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
    :param (optional kwarg) evalresp= pandas dataframe of FAP from evalresp (freq,amp,phase)
    :return: tuple of GeneralValueMetrics, corrected PSD, and PDF
    """
    R_function = robjects.r('IRISMustangMetrics::PSDMetric')
    pandas2ri.activate()
   
    # look for optional parameter evalresp=pd.DataFrame
    evalresp = None
    if 'evalresp' in kwargs:
        evalresp = kwargs['evalresp']
    
    r_listOfLists = None    
    if evalresp is not None:
        r_evalresp = pandas2ri.py2ri(evalresp)  # convert to R dataframe
        r_listOfLists = R_function(r_stream, r_evalresp)
    else:
        r_listOfLists = R_function(r_stream)
        
    r_metriclist = r_listOfLists[0]
    r_dataframe = _R_metricList2DF(r_metriclist)
    df = pandas2ri.ri2py(r_dataframe)
    
    # Convert columns from R POSIXct to python UTCDateTime
    df.starttime = df.starttime.apply(UTCDateTime)
    df.endtime = df.endtime.apply(UTCDateTime)
    
    # TODO:  What to do about the list of spectraMetrics?
    # TODO:  We would need a new R_spectrumMetricList2DF function to process this further.
    ###r_spectrumList = r_listOfLists[1] ## this would be uncorrected PSD
    
    # psd_corrected is returned as a dataframe
    r_PSDCorrected = r_listOfLists[2]
    PSDCorrected = pandas2ri.ri2py(r_PSDCorrected)
    
    # Convert columns from R POSIXct to pyton UTCDateTime
    PSDCorrected.starttime = PSDCorrected.starttime.apply(UTCDateTime)
    PSDCorrected.endtime = PSDCorrected.endtime.apply(UTCDateTime)

    r_PDF = r_listOfLists[3]
    PDF = pandas2ri.ri2py(r_PDF)
    pandas2ri.deactivate()
    
    return (df, PSDCorrected, PDF)


def apply_PSD_plot(r_stream, filepath, evalresp=None):
    """"
    Create a PSD plot which will be written to a .png file
    opened 'png' file.
    :param r_stream: an r_stream object
    :param filepath: file path for png output
    :param evalresp: (optional) pandas dataframe of FAP from evalresp (freq,amp,phase)
    :return:
    """
    result = robjects.r('grDevices::png')(filepath)
    r_psdList = robjects.r('IRISSeismic::psdList')(r_stream)
    pandas2ri.activate()
    
    # convert pandas df to R df as parameter automatically 
    if evalresp is not None:
        r_evalresp = pandas2ri.py2ri(evalresp)  # convert to R dataframe
        result = robjects.r('IRISSeismic::psdPlot')(r_psdList, style='pdf', evalresp=r_evalresp)
    else:
        result = robjects.r('IRISSeismic::psdPlot')(r_psdList, style='pdf')
    
    pandas2ri.deactivate()
    result = robjects.r('grDevices::dev.off')()

    return True



# -----------------------------------------------------------------------------


if __name__ == '__main__':
    import doctest
    print(doctest.testmod(exclude_empty=True))
