from ispaq.irismustangmetrics.metrics import *


def validate(custom_metric_sets, metric_functions=metricslist()):
    """
    :param metric_functions: a dictionary of metrics and the functions that produce
    them
    :param custom_metric_sets: dictionary of custom metric sets
    custom metric sets and returns the necesary metric
    functions and an error list
    """
    print('Validating custom metrics...')
    error_list = []
    custom_metricset_functions = {}

    # Creates a dictionary of {needed functions: [list of needed metrics that they provide]}
    for custom_metricset in custom_metric_sets:
        required_functions = {}
        for metric in custom_metric_sets[custom_metricset]:
            try:  # check if metric exists
                function = metric_functions[metric]
            except KeyError:
                print('\033[93m   Metric "%s" not found\033[0m' % metric)
                error_list.append(metric)

            if function in required_functions:
                required_functions[function].append(metric)
            else:
                required_functions[function] = [metric]

        custom_metricset_functions[custom_metricset] = required_functions

    print('Finished validating with \033[93m%d\033[0m errors.\n' % len(error_list))
    return custom_metricset_functions, error_list


def simpleset(metric_set, custom_metric_set_functions, r_streams,
              function_metadata=functionmetadata()):
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
        df = simpleMetricsPretty(df, sigfigs=6)
        return df

    elif metric_set in custom_metric_set_functions:  # if a custom metric-set
        metric_set_functions = custom_metric_set_functions[metric_set]
        df_peices = r_streams.apply(lambda r_stream: _buildcustom(r_stream, metric_set_functions))
        df = pd.concat(df_peices.tolist())
        df = df.reset_index(drop=True)  # make indices make sense        
        df = simpleMetricsPretty(df, sigfigs=6)
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
