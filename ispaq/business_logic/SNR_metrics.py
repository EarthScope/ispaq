"""
ISPAQ Business Logic for SMR Metrics.

:copyright:
    Mazama Science
:license:
    GNU Lesser General Public License, Version 3
    (http://www.gnu.org/copyleft/lesser.html)
"""
from obspy import UTCDateTime
from obspy.clients.fdsn import Client

from ispaq.concierge.concierge import Concierge

###from ispaq.irisseismic.stream import get_R_Stream_property
from ispaq.irisseismic.webservices import R_getSNCL, getEvent

from ispaq.irismustangmetrics import apply_simple_metric

import math

import pandas as pd


def generate_SNR_metrics(concierge, verbose=False):
    """
    Generate *SNR* metrics.

    :type concierge: :class:`~ispaq.concierge.Concierge`
    :param concierge: Data access expiditer.
    
    :rtype: pandas dataframe
    :return: Dataframe of simple metrics.

    .. rubric:: Example

    TODO:  doctest examples
    """
    
    # Default parameters from IRISMustangUtils::generateMetrics_SNR
    minmag = 5.5
    maxradius = 180
    windowSecs = 60
        
    # Get the seismic events in this time period
    ###events <- IRISSeismic::getEvent(iris, starttime, endtime, minmag=minmag)
    events = concierge.get_event()
        
    # Container for all of the metrics dataframes generated
    dataframes = []

    ## ----- All UN-available SNCLs ----------------------------------------------

    ## TODO:  Create percent_availability metric with   0% available

    ## ----- All available SNCLs -------------------------------------------------
    

    ## function metadata dictionary
    #simple_function_meta = concierge.function_by_logic['simple']
    
    ## loop over available SNCLS
    #for sncl in concierge.get_sncls():
        
        #(network, station, location, channel) = sncl.split('.')
        
        #if verbose: print('Calculating simple metrics for ' + sncl)

        ## Get the data ----------------------------------------------

        ## NOTE:  Use the requested starttime, not just what is available
        #try:
            #r_stream = R_getSNCL(concierge.dataselect_url, sncl, concierge.requested_starttime, concierge.requested_endtime)
        #except Exception as e:
            #if verbose: print('\n*** Unable to obtain data for %s from %s ***\n' % (sncl, concierge.dataselect_url))
            #df = pd.DataFrame({'metricName': 'percent_available',
                               #'value': 0,
                               #'snclq': snclq+'.M',
                               #'starttime': concierge.requested_starttime,
                               #'endtime': concierge.requested_endtime,
                               #'qualityFlag': -9}) 
            #dataframes.append(df)
            #continue


        ## Run the Gaps metric ----------------------------------------

        #if simple_function_meta.has_key('gaps'):
            #try:
                #df = apply_simple_metric(r_stream, 'gaps')
                #dataframes.append(df)
            #except Exception as e:
                #if verbose: print('\n*** ERROR in "gaps" metric calculation for %s ***\n' % (sncl))
                
                
        ## Run the State-of-Health metric -----------------------------

        #if simple_function_meta.has_key('stateOfHealth'):
            #try:
                #df = apply_simple_metric(r_stream, 'stateOfHealth')
                #dataframes.append(df)
            #except Exception as e:
                #if verbose: print('\n*** ERROR in "stateOfHealth" metric calculation for %s ***\n' % (sncl))
                            
            
        ## Run the Basic Stats metric ---------------------------------

        #if simple_function_meta.has_key('basicStats'):
            #try:
                #df = apply_simple_metric(r_stream, 'basicStats')
                #dataframes.append(df)
            #except Exception as e:
                #if verbose: print('\n*** ERROR in "basicStats" metric calculation for %s ***\n' % (sncl))
                            
       
        ## Run the STALTA metric --------------------------------------
       
        ## NOTE:  To improve performance, we do not calculate STA/LTA at every single point in 
        ## NOTE:  high resolution data.  Instead, we calculate STA/LTA at one point and then skip
        ## NOTE:  ahead a few points as determined by the "increment" parameter.
        ## NOTE:  An increment that translates to 0.2-0.5 secs seems to be a good compromise
        ## NOTE:  between performance and accuracy.
    
        #if simple_function_meta.has_key('STALTA'):
            
            ## TODO:  Should we limit STALTA channels?
            ## Limit this metric to BH. and HH. channels
            ## if channel.startswith('BH') or channel.startswith('HH'):
            #sampling_rate = get_R_Stream_property(r_stream, 'sampling_rate')
            #increment = math.ceil(sampling_rate/2)
            
            #try:
                #df = apply_simple_metric(r_stream, 'STALTA', staSecs=3, ltaSecs=30, increment=increment, algorithm='classic_LR')
                #dataframes.append(df)
            #except Exception as e:
                #if verbose: print('\n*** ERROR in "STALTA" metric calculation for %s ***\n' % (sncl))
            
            
        ## Run the Spikes metric --------------------------------------

        ## NOTE:  Appropriate values for spikesMetric arguments are determined empirically
            
        #if simple_function_meta.has_key('spikes'):
       
            #windowSize = 41
            #thresholdMin = 7
            #selectivity = 0.5
       
            ## Lower resolution channels L.. need a higher thresholdMin
            #sampling_rate = get_R_Stream_property(r_stream, 'sampling_rate')
            #if sampling_rate >= 1:
                #thresholdMin = 12
    
            #try:
                #df = apply_simple_metric(r_stream, 'spikes', windowSize, thresholdMin, selectivity)
                #dataframes.append(df)
            #except Exception as e:
                #if verbose: print('\n*** ERROR in "spikes" metric calculation for %s ***\n' % (sncl))            
                

    # Concatenate and filter dataframes before returning -----------------------
    
    # Create a boolean mask for filtering the dataframe
    def valid_metric(x):
        return x in concierge.metric_names
        
    result = pd.concat(dataframes, ignore_index=True)    
    mask = result.metricName.apply(valid_metric)
    result = result[(mask)]
    result.reset_index(drop=True, inplace=True)
    
    return(result)


#     R --> Python conversion functions    -------------------------------------

# TODO:  Why didn't this work inside of the irisseismic.stream module?

def get_R_Stream_property(r_stream, prop):
    """
    Return a property from the R_Stream.
    :param r_stream: IRISSeismic Stream object.
    :param prop: Name of slot in r_stream or r_stream@traces[[1]]@stats
    :return: value contained in the named property (aka 'slot')
    """
    # IRISSeismic slots as of 2016-04-07
    
    # stream_slots = r_stream.slotnames()
    #  * url
    #  * requestedStarttime
    #  * requestedEndtime
    #  * act_flags
    #  * io_flags
    #  * dq_flags
    #  * timing_qual
    #  * traces
    
    # trace_slots = r_stream.do_slot('traces')[0].slotnames()
    #  * stats
    #  * Sensor
    #  * InstrumentSensitivity
    #  * InputUnits
    #  * data
    
    # stats_slots = r_stream.do_slot('traces')[0].do_slot('stats').slotnames()
    #  * sampling_rate
    #  * delta
    #  * calib
    #  * npts
    #  * network
    #  * location
    #  * station
    #  * channel
    #  * quality
    #  * starttime
    #  * endtime
    #  * processing
    
    # Here we specify only those slots with single valued strings or floats
    stream_slots = ['url']
    
    trace_slots = ['id','Sensor','InstrumentSensitivity','InputUnits']
    
    r_stats_slots = r_stream.do_slot('traces')[0].do_slot('stats').slotnames() # <type 'rpy2.rinterface.StrSexpVector'>
    stats_slots = list(r_stats_slots) # <type 'list'>
    stats_slots.remove('starttime') # does not apply to entire r_stream
    stats_slots.remove('endtime') # does not apply to entire r_stream
    
    if prop in stream_slots:
        val = r_stream.do_slot(prop)[0]
    elif prop in trace_slots:
        val = r_stream.do_slot('traces')[0].do_slot(prop)[0]
    elif prop in stats_slots:
        val = r_stream.do_slot('traces')[0].do_slot('stats').do_slot(prop)[0]
    else:
        print('Property %s not handled yet.' % prop)
        raise
    
    return(val)


# ------------------------------------------------------------------------------


if __name__ == '__main__':
    import doctest
    doctest.testmod(exclude_empty=True)