def _remove_comments(line):
    line = line.split("#")
    return line[0].strip()


def _read_entry(entry):
    entry = entry.split(':')
    if len(entry) <= 1:
        return None, None
    name = entry[0]
    values = entry[1].strip().split(',')
    values = [value.strip() for value in values]
    values = filter(None, values) # remove empty strings
    return (name, values)

def loader(pref_loc): 
    try:  # check if file exists
        from os.path import expanduser
        pref_loc = expanduser(pref_loc)
        pref_file = open(pref_loc, 'r')
        print('Loading preferences from %s...' % pref_loc)
    except AttributeError:
        print(sys.exc_info())
        print('No user preferences discovered. Ignoring...\n')
        return None
    
    custom_metric_sets, custom_sncl = {}, {}
    current = None
    for line in pref_file: # parse file
        line = _remove_comments(line);
        
        if line.lower() == "custom metric sets:":
            current = 'm'
        elif line.lower() == "sncl aliases:":
            current = 's'
        elif current != None:
            name, values = _read_entry(line)
            if name == None:
                pass
            elif current == 'm':
                custom_metric_sets[name] = values
            elif current == 's':
                custom_sncl[name] = values
    
    print('Preferences loaded.\n')  
    
    return custom_metric_sets, custom_sncl
            

if __name__ == "__main__":
    loader("~/demo.irsp")