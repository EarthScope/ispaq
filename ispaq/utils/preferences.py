import sys
from ispaq.irismustangmetrics.metrics import metricslist


def _read_entry(entry):
    entry = entry.split(':')
    if len(entry) <= 1:
        return None, None
    name = entry[0]
    values = entry[1].strip().split(',')
    values = [value.strip() for value in values]
    values = filter(None, values)  # remove empty strings
    return name, values


def load(pref_file):
    """
    loads a preference file
    :param pref_file: the location of the preference file
    :returns: a metric set dictionary {metric_set_name: [metrics]} and a sncl dict 
    {sncl_alias: [sncls]}
    """
    
    custom_metric_sets, custom_sncl = {}, {}
    current = None
    for line in pref_file:  # parse file
        line = line.split('#')[0].strip()
        
        if line.lower() == "custom metric sets:":
            current = 'm'
        elif line.lower() == "sncl aliases:":
            current = 's'
        elif current is not None:
            name, values = _read_entry(line)
            if name is None:
                pass
            elif current == 'm':
                custom_metric_sets[name] = values
            elif current == 's':
                custom_sncl[name] = values
    
    print('Preferences loaded.\n')  
    
    return custom_metric_sets, custom_sncl


def validate_metric_sets(custom_metric_sets, metric_functions=metricslist()):
    """
    :param metric_functions: a dictionary of metrics and the functions that produce
    them
    :param custom_metric_sets: dictionary of custom metric sets
    custom metric sets and returns the necessary metric
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


def validate_file():
    """Function that could be called from cmd to verify that the given preference file shouldn't break things"""
    pass
            

if __name__ == "__main__":
    metrics, sncls = load("~/Documents/repos/ISPAQ/preference_files/cleandemo.irsp")
    print(metrics)
    print(sncls)
