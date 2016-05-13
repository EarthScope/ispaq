"""
ISPAQ Data Access Expediter.

:copyright:
    Mazama Science
:license:
    GNU Lesser General Public License, Version 3
    (http://www.gnu.org/copyleft/lesser.html)
"""

import pandas as pd

from obspy import UTCDateTime

def write_simple_df(df, filepath, sigfigs=6):
    """
    Write a pretty dataframe with appropriate significant figures to a .csv file.
    :param df: Dataframe of simpleMetrics.
    :param filepath: File to be created.
    :param sigfigs: Number of significant figures to use.
    :return: status
    """
    # Get pretty values
    pretty_df = format_simple_df(df, sigfigs=sigfigs)
    # Reorder columns, putting non-standard columns at the end and omitting 'qualityFlag'
    columns = ['snclq','starttime','endtime','metricName','value']
    original_columns = pretty_df.columns
    extra_columns = list( set(original_columns).difference(set(columns)) )
    extra_columns.remove('qualityFlag')
    columns.extend(extra_columns)
    # Write out .csv file
    pretty_df[columns].to_csv(filepath, index=False)
    
    # No return value


def format_simple_df(df, sigfigs=6):
    """
    Create a pretty dataframe with appropriate significant figures.
    :param df: Dataframe of simpleMetrics.
    :param sigfigs: Number of significant figures to use.
    :return: Dataframe of simpleMetrics.
    
    The following conversions take place:
    
    * Round the 'value' column to the specified number of significant figures.
    * Convert 'starttime' and 'endtime' to python 'date' objects.
    """
    # TODO:  Why is type(df.value[0]) = 'str' at this point?
    format_string = "." + str(sigfigs) + "g"
    df.value = df.value.astype(float)
    df.value = df.value.apply(lambda x: format(x, format_string))
    if 'starttime' in df.columns:
        df.starttime = df.starttime.apply(lambda x: x.isoformat())
    if 'endtime' in df.columns:
        df.endtime = df.endtime.apply(lambda x: x.isoformat())
    # NOTE:  df.time from SNR metric is already a string, otherwise it is NA
    #if 'time' in df.columns:
        #df.time = df.time.apply(lambda x: x.format_iris_web_service())
    if 'qualityFlag' in df.columns:
        df.qualityFlag = df.qualityFlag.astype(int)

    return df   

    
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
