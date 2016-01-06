# -*- coding: utf-8 -*-
#
# Testing the R_IRISSeismic package.

from obspy.core import UTCDateTime
from obspy.fdsn import Client

from R_IRISSeismic import R_createTraceHeader, R_createTrace

# Create a new IRIS client
client = Client("IRIS")

# Get the seismic signal
t1 = UTCDateTime("2002-04-20")
t2 = UTCDateTime("2002-04-21")
stream = client.get_waveforms('US', 'OXF', '', 'BHZ', t1, t2)

trace = stream.traces[2]

stats = trace.stats

R_TraceHeader = R_createTraceHeader(stats)

print("Obspy version")
print(stats)
print("")

print("IRISSeismic version")
print(R_TraceHeader)
print("")

R_Trace = R_createTrace(trace)
