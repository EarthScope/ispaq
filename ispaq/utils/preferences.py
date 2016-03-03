import sys


def _remove_comments(line):
    '''removes a comment from a given single line string'''
    line = line.split("#")
    return line[0].strip()


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
    '''
    loads a preference file
    :param pref_loc: the location of the preference file
    :returns: a metric set dictionary {metric_set_name: [metrics]} and a sncl dict 
    {sncl_alias: [sncls]}
    '''
    
    custom_metric_sets, custom_sncl = {}, {}
    current = None
    for line in pref_file:  # parse file
        line = _remove_comments(line)
        
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

def validate():
    '''Function that could be called from cmd to verify that the given preference file shouldn't break things'''
    pass
            

if __name__ == "__main__":
    metrics, sncls = load("~/Documents/repos/ISPAQ/ispaq/preference_files/cleandemo.irsp")
    print(metrics)
    print(sncls)
