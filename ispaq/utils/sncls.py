import pandas as pd


def get_simple_sncls(sncl_alias, custom_sncls, starttime, endtime):
    """
    returns the simplest sncls that compose any sncl or sncl alias
    :param sncl_alias: any sncl or sncl alias
    :param custom_sncls: a dictonary {sncl_alias: [list of sncls]}
    :param starttime: start of period to decompose over
    :param endtime: end of period to decompose over
    :returns: a pandas series of simple sncls (as strings)
    """
    if _validate(sncl_alias): 
        return _decompose(sncl_alias, starttime, endtime)
    elif sncl_alias in custom_sncls:
        simple_sncls = pd.concat([_decompose(sncl, starttime, endtime) for sncl in custom_sncls[sncl_alias]])
        return simple_sncls.reset_index(drop=True)


def _decompose(sncl, startime, endtime):
    """
    Validates complex sncl for a given date period and returns a list of simpler sncls
    :param sncl: sncl to decompose
    :param startime: start of period to decompose over
    :param endtime: end of period to decompose over
    :return: a pandas series of simple sncls (as strings)
    """
    
    from ispaq.irisseismic.webservices import getAvailability
    channel_metadata = getAvailability(sncl, startime, endtime).reset_index(drop=True)
    return channel_metadata['snclId']


def _validate(sncl):
    """
    Validates that a given string is a sncl
    
    >>> _validate('US.OXF..BH?')
    True
    >>> _validate('...')
    True
    >>> _validate('*.OXF.*.BH?')
    True
    >>> _validate('')
    False
    >>> _validate('.*.*.HGFD4')
    False
    >>> _validate('fkfkf.*.*.BH?')
    False
    """
    import re
    return re.match('^\S{0,3}\.\S{0,4}\.\S{0,3}\.\S{0,3}$', sncl) is not None


def build(sncl_dict):  # TODO potentially no longer useful
    """
    Builds complex sncls from dictionary
    :param sncl_dict: a dictionary {snclalias:{network:n,station:s,location:l,channel:c}}
    :return: a dictionary {snclalias:sncl}
    """
    
    returndict = {}
    for alias in sncl_dict:
        sub = sncl_dict[alias]
        returndict[alias] = '%s.%s.%s.%s' % (sub['Network'], sub['Station'],
                                             sub['Location'], sub['Channel'])
        
    return returndict


if __name__ == "__main__":
    import doctest
    print(doctest.testmod(exclude_empty=True))
