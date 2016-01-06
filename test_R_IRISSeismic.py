# -*- coding: utf-8 -*-
#
# Testing the R_IRISSeismic package.

from obspy.core import UTCDateTime
from obspy.fdsn import Client

from R_IRISSeismic import R_createTraceHeader, R_createTrace, R_createStream
from R_IRISMustangMetrics import R_basicStatsMetric, R_gapsMetric

# Create a new IRIS client
client = Client("IRIS")

# Get the seismic signal
t1 = UTCDateTime("2002-04-20")
t2 = UTCDateTime("2002-04-21")
stream = client.get_waveforms('US', 'OXF', '', 'BHZ', t1, t2)

R_Stream = R_createStream(stream)

basicStats = R_basicStatsMetric(R_Stream)
print(basicStats)

gaps = R_gapsMetric(R_Stream)
print(gaps)
