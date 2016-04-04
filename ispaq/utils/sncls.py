import pandas as pd


def get_simple_sncls(user_request):
    """
    returns the simplest sncls that compose any sncl or sncl_set
    :param sncl_set: any sncl or sncl_set
    :param custom_sncls: a dictonary {sncl_set: [list of sncls]}
    :param starttime: start of period to decompose over
    :param endtime: end of period to decompose over
    :returns: a pandas series of simple sncls (as strings)
    """
    if _validate(user_request.requested_sncl_set):
        return _decompose(user_request.requested_sncl_set, user_request.requested_starttime,
                          user_request.requested_endtime)
    elif user_request.requested_sncl_set in user_request.sncl_sets:
        simple_sncls = pd.concat([_decompose(sncl, user_request.requested_starttime,
                                             user_request.requested_endtime)
                                  for sncl in user_request.sncl_sets[user_request.requested_sncl_sets]])
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
    :param sncl_dict: a dictionary {sncl_set:{network:n,station:s,location:l,channel:c}}
    :return: a dictionary {sncl_set:sncl}
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
