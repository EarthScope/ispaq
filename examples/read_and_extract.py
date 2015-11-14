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

if False:
    
    # Example from: http://docs.obspy.org/packages/obspy.fdsn.html#module-obspy.fdsn
    
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
    
    