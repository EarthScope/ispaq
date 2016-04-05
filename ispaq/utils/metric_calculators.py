"""I imagine that this file will contain the business logic to calculate all the different sorts of metric sets"""


from ispaq.irismustangmetrics.metrics import *


# TODO make this function accept a UserRequests object
def simple_set(metric_set, custom_metric_set_functions, r_streams, sigfigs=6,
               function_metadata=function_metadata()):
    """
    Returns a dataframe with the metrics specified in the metric_set
    :param r_streams: pandas series of r_streams
    :param function_metadata: the metadata of all the default metric sets
    :param custom_metric_set_functions: dictionary of needed functions (see validateCustomMetricSets)
    :param metric_set: the desired set of metrics
    :returns: a dataframe with the desired metrics
    """
    import pandas as pd    

    if metric_set in function_metadata:  # if a preset metric-set
        df_peices = r_streams.apply(lambda r_stream: applySimpleMetric(r_stream, metric_set))
        df = pd.concat(df_peices.tolist())
        df = df.reset_index(drop=True)  # make indices make sense
        # Create a pretty version of the dataframe
        df = simpleMetricsPretty(df, sigfigs=sigfigs)
        return df

    elif metric_set in custom_metric_set_functions:  # if a custom metric-set
        metric_set_functions = custom_metric_set_functions[metric_set]
        df_peices = r_streams.apply(lambda r_stream: _buildcustom(r_stream, metric_set_functions))
        df = pd.concat(df_peices.tolist())
        df = df.reset_index(drop=True)  # make indices make sense        
        df = simpleMetricsPretty(df, sigfigs=sigfigs)
        return df

    print('\033[93mMetric Set "%s" not found\033[0m' % metric_set)
    return None


def _buildcustom(r_stream, metric_set_functions):
    """Builds a df for an individual r_stream given the needed functions for a custom metric_set"""
    df_peices = []    
    for function in metric_set_functions:
        tempdf = applySimpleMetric(r_stream, function)
        tempdf = tempdf.loc[tempdf['metricName'].isin(metric_set_functions[function])]
        df_peices.append(tempdf)    
    df = pd.concat(df_peices)
    return df
