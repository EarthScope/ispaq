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
* return type (single values, multiple values, times, spectra, *etc.*)

Functions in the IRISMustangMetrics R package provide this metadata so that
functions can be called programmatically from python without the user having
to know anything about the particular metric function they are calling.
"""

import math
import numpy as np
import pandas as pd
import json

from obspy.core import UTCDateTime

from rpy2 import robjects
import rpy2.robjects as ro
from rpy2 import rinterface
from rpy2.robjects import pandas2ri
from rpy2.robjects import numpy2ri
from rpy2.robjects.packages import importr
from rpy2.robjects.conversion import localconverter

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


def apply_simple_metric(av, starttime, endtime, r_stream, metric_function_name, *args, **kwargs):
    """"
    Invoke a named "simple" R metric and convert the R dataframe result into
    a Pandas dataframe.
    :param r_stream: an r_stream object
    :param metric_function_name: the name of the set of metrics
    :return:
    """
    
    
#     if metric_function_name is 'numSpikes':
    if metric_function_name == 'numSpikes':
        function = 'IRISMustangMetrics::spikesMetric'
    else:
        function = 'IRISMustangMetrics::' + metric_function_name + 'Metric'
        
    R_function = robjects.r(function)
    try:
        r_metriclist = R_function(r_stream, *args, **kwargs)
        r_dataframe = _R_metricList2DF(r_metriclist)
        
        # Convert to a pandas dataframe
        pandas2ri.activate()
        df = ro.conversion.rpy2py(r_dataframe)
        pandas2ri.deactivate()
        
    except:
        # The stream being empty will trigger this, so mark percent_Availability=0
#         snclq = av.snclId + '.M'    # Obsolete now that new logic is in place in simple_metrics.py
        df = pd.DataFrame(columns=['metricName','snclq','starttime','endtime','qualityFlag','value'])
        
        df.loc[len(df.index)] = ['percent_availability',snclq, starttime, endtime, -9, 0 ]
    
    # Convert columns from R POSIXct to python UTCDateTime
    df.starttime = df.starttime.apply(UTCDateTime)
    df.endtime = df.endtime.apply(UTCDateTime)
    
    return df

def apply_sampleRateResp_metric(r_stream,resp_pct,norm_freq,evalresp):
    """"
    Invoke the sampleRateResp R metric and convert the R dataframe result into
    a Pandas dataframe.
    :param r_stream: an r_stream object
    :param resp_pct: percent deviation allowed for sample_rate_resp
    :param: norm_freq: SensitivityFrequency from the data
    :param evalresp: None if from webservices, pandas evalresp if local
    :return:
    """

    function = 'IRISMustangMetrics::sampleRateRespMetric'
    R_function = robjects.r(function)

    #kwargs is just evalresp, if none is provided then the R code will go to IRIS to get it anyway
    if evalresp is not None:
        with localconverter(ro.default_converter + pandas2ri.converter):
            r_evalresp = ro.conversion.py2rpy(evalresp)

        r_metriclist = R_function(r_stream,resp_pct,norm_freq, r_evalresp)
    else:
        r_metriclist = R_function(r_stream,resp_pct,norm_freq)

    r_dataframe = _R_metricList2DF(r_metriclist)

    # Convert to a pandas dataframe
    pandas2ri.activate()
    df = ro.conversion.rpy2py(r_dataframe)
    pandas2ri.deactivate()

    # Convert columns from R POSIXct to python UTCDateTime
    df.starttime = df.starttime.apply(UTCDateTime)
    df.endtime = df.endtime.apply(UTCDateTime)

    return df

def apply_sampleRateChannel_metric(r_stream, channel_pct,chan_rate):
    """"
    Invoke the sampleRateChannel R metric and convert the R dataframe result into
    a Pandas dataframe.
    :param r_stream: an r_stream object
    :param channel_pct: percent deviation allowed for sample_rate_channel 
    :param chan_rate: metadata-derived sample rate
    :param evalresp: None if from webservices, pandas evalresp if local
    :return:
    """
    
    function = 'IRISMustangMetrics::sampleRateChannelMetric'
    R_function = robjects.r(function)

    r_metriclist = R_function(r_stream,channel_pct,chan_rate)
        
    r_dataframe = _R_metricList2DF(r_metriclist)

    # Convert to a pandas dataframe
    pandas2ri.activate()
    df = ro.conversion.rpy2py(r_dataframe)
    pandas2ri.deactivate()
    
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
    r_metriclist = R_function(r_stream1, r_stream2, *args, **kwargs) 
    pandas2ri.deactivate()
    
    r_dataframe = _R_metricList2DF(r_metriclist)

    pandas2ri.activate()
    df = ro.conversion.rpy2py(r_dataframe)
    pandas2ri.deactivate()
    
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
    
    # NOTE:  Conversion of dataframes only works if you activate but we don't want conversion
    # NOTE:  to always be automatic so we deactivate() after we're done converting.

    with localconverter(ro.default_converter + pandas2ri.converter):
        r_evalresp1 = ro.conversion.py2rpy(evalresp1)
        r_evalresp2 = ro.conversion.py2rpy(evalresp2)

    # TODO:  Can we just activate/deactivate before/after R_function() without converting
    # TODO:  r_evalresp1/2 ahead of time?
    
    # Calculate the metric
    r_metriclist = R_function(r_stream1, r_stream2, r_evalresp1, r_evalresp2)
    r_dataframe = _R_metricList2DF(r_metriclist)

    pandas2ri.activate()
    df = ro.conversion.rpy2py(r_dataframe)
    pandas2ri.deactivate()
    
    # Convert columns from R POSIXct to pyton UTCDateTime
    df.starttime = df.starttime.apply(UTCDateTime)
    df.endtime = df.endtime.apply(UTCDateTime)
    return df

#     Functions for PSDMetrics     ---------------------------------------------

def apply_PSD_metric(concierge, r_stream, *args, **kwargs):
    """"
    Invoke the PSDMetric and convert the R dataframe result into
    a Pandas dataframe.
    :param r_stream: an r_stream object
    :param (optional kwarg) evalresp= pandas dataframe of FAP from evalresp (freq,amp,phase)
    :return: tuple of GeneralValueMetrics, corrected PSD, and PDF
    """
    
    R_function = robjects.r('IRISMustangMetrics::PSDMetric')

    # look for optional parameter evalresp=pd.DataFrame
    evalresp = None
    if 'evalresp' in kwargs:
        evalresp = kwargs['evalresp']
        
    r_listOfLists = None
    r_evalresp = evalresp
    if  evalresp is not None:
        with localconverter(ro.default_converter + pandas2ri.converter):
            ###################
            r_evalresp = ro.conversion.py2rpy(evalresp)
            ###################
        r_listOfLists = R_function(r_stream, evalresp=r_evalresp)
    else:
        concierge.logger.debug('calling IRIS evalresp web service')
        r_listOfLists = R_function(r_stream)

    r_metriclist = r_listOfLists[0]
    
    if r_metriclist:
        r_dataframe = _R_metricList2DF(r_metriclist)

        with localconverter(ro.default_converter + pandas2ri.converter):
            df = ro.conversion.rpy2py(r_dataframe)

        # Convert columns from R POSIXct to python UTCDateTime
        df['starttime'] = df['starttime'].apply(UTCDateTime)
        df['endtime'] = df['endtime'].apply(UTCDateTime)

    # PSDMetric returns no PSD derived metrics 
    else:    
        df = pd.DataFrame()
    
    # correctedPSD is returned as a dataframe
    r_correctedPSD = r_listOfLists[2]
    with localconverter(ro.default_converter + pandas2ri.converter):
        PSDCorrected = ro.conversion.rpy2py(r_correctedPSD)

    # Convert columns from R POSIXct to python UTCDateTime
    PSDCorrected.starttime = PSDCorrected.starttime.apply(UTCDateTime)
    PSDCorrected.endtime = PSDCorrected.endtime.apply(UTCDateTime)

    r_PDF = r_listOfLists[3]
    with localconverter(ro.default_converter + pandas2ri.converter):
        PDF = ro.conversion.rpy2py(r_PDF)

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
   
    if len(r_psdList) == 0:
        raise Exception("No PSDs returned")
   
    pandas2ri.activate()
    
    # convert pandas df to R df as parameter automatically
    if evalresp is not None:
#         with localconverter(robjects.default_converter + pandas2ri.converter):
#             r_evalresp = robjects.conversion.py2rpy(evalresp)
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
