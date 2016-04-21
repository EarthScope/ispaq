"""
ISPAQ Data Access Expediter.

:copyright:
    Mazama Science
:license:
    GNU Lesser General Public License, Version 3
    (http://www.gnu.org/copyleft/lesser.html)
"""
# Use UTCDateTime internally for all times
from obspy import UTCDateTime

import pandas as pd



#     R --> Python conversion functions    ---------------------------------
    
def get_slot(r_object, prop):
    """
    Return a property from the R_Stream.
    :param r_object: IRISSeismic Stream, Trace or TraceHeader object
    :param prop: Name of slot in the R object or any child object
    :return: python version value contained in the named property (aka 'slot')
    
    This convenience function allows business logic code to easily extract
    any property that is an atomic value in one of the R objects defined in
    the IRISSeismic R package.
    
    IRISSeismic slots as of 2016-04-07
    
    stream_slots = r_stream.slotnames()
     * url
     * requestedStarttime
     * requestedEndtime
     * act_flags
     * io_flags
     * dq_flags
     * timing_qual
     * traces
    
    trace_slots = r_stream.do_slot('traces')[0].slotnames()
     * stats
     * Sensor
     * InstrumentSensitivity
     * InputUnits
     * data
    
    stats_slots = r_stream.do_slot('traces')[0].do_slot('stats').slotnames()
     * sampling_rate
     * delta
     * calib
     * npts
     * network
     * location
     * station
     * channel
     * quality
     * starttime
     * endtime
     * processing
    """
    
    slotnames = list(r_object.slotnames())
    
    # R Stream object
    if 'traces' in slotnames:
        if prop in ['traces']:
            # return traces as R objects
            return r_object.do_slot(prop)
        elif prop in ['requestedStarttime','requestedEndtime']:
            # return times as UTCDateTime
            return UTCDateTime(r_object.do_slot(prop)[0])
        elif prop in slotnames:
            # return atmoic types as is
            return r_object.do_slot(prop)[0]
        else:
            # looking for a property from from lower down the hierarchy
            r_object = r_object.do_slot('traces')[0]
            slotnames = list(r_object.slotnames())            
        
    # R Trace object
    if 'stats' in slotnames:
        if prop in ['stats']:
            # return stats as an R object
            return r_object.do_slot(prop)
        elif prop in ['data']:
            # return data as an array
            return list(r_object.do_slot(prop))
        elif prop in slotnames:
            # return atmoic types as is
            return r_object.do_slot(prop)[0]
        else:
            # looking for a property from from lower down the hierarchy
            r_object = r_object.do_slot('stats')
            slotnames = list(r_object.slotnames())
    
    # R TraceHeader object
    if 'processing' in slotnames:
        if prop in ['starttime','endtime']:
            # return times as UTCDateTime
            return UTCDateTime(r_object.do_slot(prop)[0])
        else:
            # return atmoic types as is
            return r_object.do_slot(prop)[0]
    
    
    # Should never get here
    print('\n*** ERROR in utils.get_slot(): "%s" is not a recognized property.***\n' % (prop))
    raise
        

if __name__ == '__main__':
    import doctest
    doctest.testmod(exclude_empty=True)
