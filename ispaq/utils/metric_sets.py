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
                print('   Metric "%s" not found' % metric)
                error_list.append(metric)

            if function in required_functions:
                required_functions[function].append(metric)
            else:
                required_functions[function] = [metric]

        custom_metricset_functions[custom_metricset] = required_functions

    print('Finished validating with %d errors.\n' % len(error_list))
    return custom_metricset_functions, error_list


def simpleset(metric_set, custom_metric_set_functions, r_stream,
              function_metadata=functionmetadata()):
    """
    Returns a dataframe with the metrics specified in the metric_set
    :param r_stream: r_stream
    :param function_metadata: the metadata of all the default metric sets
    :param custom_metric_set_functions: dictionary of needed functions (see validateCustomMetricSets)
    :param metric_set: the desired set of metrics
    :returns: a dataframe with the desired metrics
    """

    if metric_set in function_metadata:  # if a preset metric-set
        df = applySimpleMetric(r_stream, metric_set)
        # Create a pretty version of the dataframe
        df = simpleMetricsPretty(df, sigfigs=6)
        print(df)
        return df

    elif metric_set in custom_metric_set_functions:  # if a custom metric-set
        import pandas as pd
        df_peices = []
        metric_set_functions = custom_metric_set_functions[metric_set]
        for function in metric_set_functions:
            tempdf = applySimpleMetric(r_stream, function)
            tempdf = tempdf.loc[tempdf['metricName'].isin(metric_set_functions[function])]
            df_peices.append(tempdf)
        df = pd.concat(df_peices)
        print(df)
        return df

    print('Metric Set not found')
