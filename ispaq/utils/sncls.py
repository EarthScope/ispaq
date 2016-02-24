def decompose(sncl, startime, endtime):
    """
    Validates complex sncl for a given date period and returns a list of simpler sncls
    :param sncl: sncl to decompose
    :param startime: start of period to decompose over
    :param endtime: end of period to decompose over
    :return: a pandas series of simple sncls (as strings)
    """
    
    from ispaq.irisseismic.webservices import getAvailability
    return getAvailability(sncl, startime, endtime).reset_index(drop=True)['snclId']

def validate(sncl):
    """It would be useful to be able to validate whether sncls are in the correct format"""
    pass

def build(sncldict):
    """
    Builds complex sncls from dictionary
    :param sncldict: a dictionary {snclalias:{network:n,station:s,location:l,channel:c}}
    :return: a dictionary {snclalias:sncl}
    """
    
    returndict = {}
    for alias in sncldict:
        sub = sncldict[alias]
        returndict[alias] = '%s.%s.%s.%s' % (sub['Network'], sub['Station'],
                                             sub['Location'], sub['Channel'])
        
    return returndict