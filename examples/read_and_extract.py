# coding: utf8

from obspy.core import read

import sys

# myfile = sys.argv[1]
# st = read(myfile)

st = read('http://examples.obspy.org/RJOB_061005_072159.ehz.new')

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


# -----
# Getting Data from IRIS web services
#
# NOTE:  Need to run with non-default /opt/local/bin/python2.7 which is where macports installed it.
# NOTE:
# NOTE:  The macports installation was helpful in getting R and rpy2 to run but I am getting the
# NOTE:  following error message when trying to import obspy.core.UTCDateTime
# NOTE:
# NOTE:      LookupError: unknown encoding:

# Default R installation is in /usr/bin/R

# Anaconda R installation (where obspy works, but R doesn't yet) is /Users/jonathancallahan/miniconda2/bin/python2.7

# Various installation issues to be worked out just for OSX
# (Potential "Ugh" for other systems!)



if False:
    

    from obspy.core import UTCDateTime
    from obspy.fdsn import Client
    client = Client("IRIS")
    
    # ----- From the ObsPy example
    
    #from obspy.fdsn.header import URL_MAPPINGS
    #for key in sorted(URL_MAPPINGS.keys()):
        #print("{0:<7} {1}".format(key,  URL_MAPPINGS[key]))
    
    #t = UTCDateTime("2013-01-03T00:00:00")
    #st = client.get_waveforms('IU', 'RAO', '10', 'BHZ', t, t + 60*60)
    
    #st.plot()
    
    # ----- Gaps
     
    t = UTCDateTime("2002-04-20")
    st = client.get_waveforms('US', 'OXF', '', 'BHZ', t, t + 24*3600)
    st.printGaps()
    
    #gapInfo = st.getGaps()
    
    