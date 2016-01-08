# -*- coding: utf-8 -*-
#
# Testing the irisseismic package.

from obspy.core import UTCDateTime
from obspy.fdsn import Client

from irisseismic import R_Stream
from irismustangmetrics import R_basicStatsMetric, R_gapsMetric

# Create a new IRIS client
client = Client("IRIS")

# Get the seismic signal
t1 = UTCDateTime("2002-04-20")
t2 = UTCDateTime("2002-04-21")
stream = client.get_waveforms('US', 'OXF', '', 'BHZ', t1, t2)

R_Stream = R_Stream(stream, t1, t2)

basicStats = R_basicStatsMetric(R_Stream)
print(basicStats)

gaps = R_gapsMetric(R_Stream)
print(gaps)
