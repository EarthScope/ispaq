# -*- coding: utf-8 -*-
# .

# An installation test script to see whether ObsPy, the rpy2 module
# along with R and the IRISSeismic packages can work in the same environment.
#
# If this script runs successfully, everything is properly installed.

try:
    
    from obspy.core import UTCDateTime
    from obspy.fdsn import Client
    client = Client("IRIS")

    t = UTCDateTime("2002-04-20")
    st = client.get_waveforms('US', 'OXF', '', 'BHZ', t, t + 24*3600)
    st.printGaps()

except:
    
    print('ERROR:  Could not run ObsPy code.')

else:
    
    print('Successfully ran ObsPy code.')

    
    
try:
    
    import rpy2.robjects as robjects
    r = robjects.r
    
    r('library(IRISSeismic)')
    
    iris = r('new("IrisClient")')
    starttime = r("as.POSIXct('2002-04-20',tz='GMT')")
    endtime = r("as.POSIXct('2002-04-21',tz='GMT')")
    
    # Get the function
    getDataselect = r('IRISSeismic::getDataselect')
    
    # Invoke the function to get a traces
    st = getDataselect(iris,"US","OXF","","BHZ",starttime,endtime)
    tr = st.do_slot('traces')[0]
    
    tr.do_slot('id')[0]
    
except:
    
    print('ERROR:  Could not run rpy2 or IRISSeismic.')
    
else:
    
    print('Sucessfully ran rpy2 and IRISSeismic.')