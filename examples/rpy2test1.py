
## Junk script for initial testing of rpy2.  This file will likely get deleted after testing is done.

try:
    import rpy2.robjects as robjects
    r = robjects.r
except Exception, e:
    status = 'ERROR'
    error_text = str(e)
    
pi = r['pi']

print pi[0]


# Jon's test calling 'seismic' packages
if False:
    
    import rpy2.robjects as robjects
    r = robjects.r
    
    # Following the example in http://mazamascience.com/Classes/IRIS_2015/Lesson_05_seismicPackages.html
    
    r('library(IRISSeismic)')
    
    iris = r('new("IrisClient")')
    starttime = r("as.POSIXct('2002-04-20',tz='GMT')")
    endtime = r("as.POSIXct('2002-04-21',tz='GMT')")
    
    # Get the function
    getDataselect = r('IRISSeismic::getDataselect')
    
    # Invoke the function to get a traces
    st = getDataselect(iris,"US","OXF","","BHZ",starttime,endtime)
    
    type(st)
    #<class 'rpy2.robjects.methods.RS4'>
    
    # Check out the S4 "slots"
    for slot in st.slotnames():
        print(slot)
        
        #url
        #requestedStarttime
        #requestedEndtime
        #act_flags
        #io_flags
        #dq_flags
        #timing_qual
        #traces
        
    st.do_slot('url')[0]
    #'http://service.iris.edu/fdsnws/dataselect/1/query?net=US&sta=OXF&loc=--&cha=BHZ&start=2002-04-20T00:00:00&end=2002-04-21T00:00:00&quality=B'
    
    # Get the traces
    traces = st.do_slot('traces')
    len(traces)
    #5
    
    # Pull out a single trace and investigate
    tr = traces[0]
    for slot in tr.slotnames():
        print(slot)
        
        #id
        #stats
        #Sensor
        #InstrumentSensitivity
        #InputUnits
        #data
        
    tr.do_slot('id')[0]
    #'US.OXF..BHZ.M'
    
    # How many data points in the first trace?
    len(tr.do_slot('data'))
    #10733
    
    stats = tr.do_slot('stats')
    for slot in stats.slotnames():
        print(slot)
        
        #delta
        #calib
        #npts
        #network
        #location
        #station
        #channel
        #quality
        #starttime
        #endtime
        #processing
        
    # Accress individual elements from the "TraceHeader" object
    stats.do_slot('starttime')[0]
    #1019260800.024
    
    stats.do_slot('sampling_rate')[0]
    #40.0
    
    #### Can we build up a TraceHeader object?
    ####
    #### From the miniseed2Stream() function in IRISSeismic/R/Utils.R we see 
    
    #headerList <- list(network=segList[[i]]$network,
                       #station=segList[[i]]$station,
                       #location=segList[[i]]$location,
                       #channel=segList[[i]]$channel,
                       #quality=segList[[i]]$quality,
                       #starttime=as.POSIXct(segList[[i]]$starttime, origin=origin, tz="GMT"),
                       #npts=segList[[i]]$npts,
                       #sampling_rate=segList[[i]]$sampling_rate)

    #stats <- new("TraceHeader", headerList=headerList)
    
    # So we need to create an R list first
    
    headerList = r('''list(network="US",
                           station="OXF",
                           location="",
                           channel="BHZ",
                           quality="M",
                           starttime=as.POSIXct('2002-04-20',tz='GMT'),
                           endtime=as.POSIXct('2002-04-21',tz='GMT'),
                           npts=10733,
                           sampling_rate=40.0)''')
    
    print(headerList)
    # looks good
    
    #### Instead of trying to create a TraceHeader in python, let R do the work following 
    #### the example R code above.
    
    # Create the headerList inside the R space
    r('''headerList <- list(network="US", 
                            station="OXF",
                            location="",
                            channel="BHZ",
                            quality="M",
                            starttime=as.POSIXct("2002-04-20",tz="GMT"),
                            endtime=as.POSIXct("2002-04-21",tz="GMT"),
                            npts=as.integer(10733),
                            sampling_rate=40.0)''')
    r('myStats <- new("TraceHeader", headerList=headerList)')
    # Test
    r('show(myStats)')
    
    # Obtain this object in the python environment
    myStats = r('get("myStats")')
    myStats.do_slot('sampling_rate')[0]
    #40.0
    
    #### Now, can we pass objects from the python space into the R space
    
    #### Having trouble bringing the R list() function into python space. Probably because
    #### it has "..." argument.
    ####
    #### How about creating a new R function specifically for creating headerList
    
    # This function creates the headerList in R and returns the R object back to python
    R_headerList = r('''function(network,station,location,channel,quality,starttime,endtime,npts,sampling_rate) {
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
    
    # We also need to be able to assign things to the R namespace
    R_assign = r('assign')
    
    # Create the list "in python"
    my_R_headerList = R_headerList("US","OXF","","BHZ","M",starttime,endtime,10733,40.0)
    
    # Now, having created the R object "in python" we can pass it to R and have it created "in R"
    returnValue = R_assign("myHeaderList",my_R_headerList) # The R object is also returned 
    
    # Demonstrate that it is there
    print(r('ls()'))
    r('str(myHeaderList)')
    
    #### But how do we get python access the S4 class "initialize" method?
    
    # Start by creating returning a new TraceHeader object to python
    my_empty_TraceHeader = r('new("TraceHeader")')
    
    # Luckily, the initialize method should recognizing the incoming first argument and dipatch to TraceHeader method
    R_initialize = r('IRISSeismic::initialize')
    my_full_TraceHeader = R_initialize(my_empty_TraceHeader, my_R_headerList)
    
    # Did it work?
    for slot in my_full_TraceHeader.slotnames():
        print(slot)
        
    my_full_TraceHeader.do_slot('network')[0]
    
    
    #### YAY!!  Demonstrated ability to create, "in python", R objects that can be used
    #### YAY!!  to create higher level S4 classes.
    



    
    
    