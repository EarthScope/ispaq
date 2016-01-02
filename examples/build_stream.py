# -*- coding: utf-8 -*-
#

# An example demonstrating that we can obtain an ObsPy Stream
# and convert it into an R_object stream.


from obspy.core import UTCDateTime
from obspy.fdsn import Client

# Create a new IRIS client
client = Client("IRIS")

# Get the seismic signal
t1 = UTCDateTime("2002-04-20")
t2 = t1 + 24*3600
st = client.get_waveforms('US', 'OXF', '', 'BHZ', t1, t2)


print(st.traces[0].stats)


# We have it so now fire up the R code


import rpy2.robjects as robjects
r = robjects.r

# Load the IRISSeismic package
r('library(IRISSeismic)')

# Create a new R_client
R_client = r('new("IrisClient")')

# Get functions to help build things up in R
R_createHeaderList = r('''
function(network,station,location,channel,quality,starttime,endtime,npts,sampling_rate) {
  list(network=network,
       station=station,
       location=location,
       channel=channel,
       quality=quality,
       starttime=starttime,
       endtime=endtime,
       npts=npts,
       sampling_rate=sampling_rate)
}''')

R_assign = r('assign')

R_asPOSIXct = r('as.POSIXct')

R_initialize = r('IRISSeismic::initialize')

# Create a TraceHeader from the ObsPy "stats" object

stats = st.traces[0].stats
starttime = R_asPOSIXct(t1.isoformat(), tz="GMT")
endtime = R_asPOSIXct(t2.isoformat(), tz="GMT")
R_headerList = R_createHeaderList(stats.network,
                                  stats.station,
                                  stats.location,
                                  stats.channel,
                                  "M",
                                  starttime,
                                  endtime,
                                  stats.npts,
                                  stats.sampling_rate)
                                            
# Create the TraceHeader
R_TraceHeader = r('new("TraceHeader")')
R_TraceHeader = R_initialize(R_TraceHeader, R_headerList)


# From the seismic package R code
###setMethod("initialize", "Trace",
  ###function(.Object,
  
           ###id="",
           ###stats=new("TraceHeader"),
           ###Sensor = "",
           ###InstrumentSensitivity = 1.0,
           ###InputUnits = "",
           ###data=c(0),
           ###...) {
    
# Create the Trace
data = robjects.vectors.FloatVector(st.traces[0].data)
R_Trace = r('new("Trace")')
R_Trace = R_initialize(R_Trace,
                       id="from_ObsPy",
                       stats=R_TraceHeader,
                       Sensor="Unknown Sensor",
                       InstrumentSensitivity=1.0,
                       InputUnits="",
                       data=data)

# Test
rms = r('IRISSeismic::rms')
bop = rms(R_Trace)[0]
print(bop)

# OR
r('IRISSeismic::mean')(R_Trace)[0]



