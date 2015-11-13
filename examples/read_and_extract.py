from obspy.core import read

import sys

myfile = sys.argv[1]

# st = read('http://examples.obspy.org/RJOB_061005_072159.ehz.new')

st = read(myfile)

print(st)

len(st)

tr = st[0]  # assign first and only trace to new variable

print(tr)

print(tr.stats)

print tr.stats.station

print(tr.stats.gse2.datatype)

print tr.data


len(tr)

st.plot()
