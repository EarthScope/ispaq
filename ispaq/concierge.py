"""
ISPAQ Data Access Expediter.

:copyright:
    Mazama Science
:license:
    GNU Lesser General Public License, Version 3
    (https://www.gnu.org/copyleft/lesser.html)
"""

import os
import sys
import re
import glob
import math
import fileinput
import fnmatch
import tempfile
import datetime

import pandas as pd
import numpy as np

from distutils.version import StrictVersion 

import obspy
from obspy.clients.fdsn import Client
from obspy.clients.fdsn.header import URL_MAPPINGS
from obspy import UTCDateTime

# ISPAQ modules
try:
    from user_request import UserRequest
    import irisseismic
    import utils
except:
    from .user_request import UserRequest
    from . import irisseismic
    from . import utils


# Custom exceptions

class NoAvailableDataError(Exception):
    """No matching data are available."""
    

class Concierge(object):
    """
    ISPAQ Data Access Expediter.

    :type user_request: :class:`~ispaq.concierge.user_request`
    :param user_request: User request containing the combination of command-line
        arguments and information from the parsed user preferences file.

    :rtype: :class:`~ispaq.concierge` or ``None``
    :return: ISPAQ Concierge.

    .. rubric:: Example

    TODO:  include doctest examples
    """
    def __init__(self, user_request=None, logger=None):
        """
        Initializes the ISPAQ data access expediter.

        See :mod:`ispaq.concierge` for all parameters.
        """
        # Keep the entire UserRequest and logger
        self.user_request = user_request
        self.logger = logger
        
        # Copy important UserRequest properties to the Concierge for simpler access
        self.requested_starttime = user_request.requested_starttime
        self.requested_endtime = user_request.requested_endtime 
        self.metric_names = user_request.metrics
        self.sncl_patterns = user_request.sncls
        self.function_by_logic = user_request.function_by_logic
        self.logic_types = user_request.function_by_logic.keys()
        
        # Individual elements from the Preferences: section of the preferences file
        
        if (os.path.isdir(user_request.csv_dir)):
            self.csv_dir = user_request.csv_dir
        else:
            self.logger.warning("csv_dir %s does not exist, creating directory" % user_request.csv_dir)
            try:
                os.makedirs(user_request.csv_dir)
                self.csv_dir = user_request.csv_dir
            except OSError as exc:
                self.logger.warning("Cannot create csv_dir %s, defaulting to current directory" % user_request.csv_dir)
                self.csv_dir = "."

        if (os.path.isdir(user_request.psd_dir)):
            self.psd_dir = user_request.psd_dir
        else:
            self.logger.warning("psd_dir %s does not exist, creating directory" % user_request.psd_dir)
            try:
                os.makedirs(user_request.psd_dir)
                self.psd_dir = user_request.psd_dir
            except OSError as exc:
                self.logger.warning("Cannot create psd_dir %s, defaulting to current directory" % user_request.psd_dir)
                self.psd_dir = "."
        
        if (os.path.isdir(user_request.pdf_dir)):
            self.pdf_dir = user_request.pdf_dir
        else:
            self.logger.warning("pdf_dir %s does not exist, creating directory" % user_request.pdf_dir)
            try:
                os.makedirs(user_request.pdf_dir)
                self.pdf_dir = user_request.pdf_dir
            except OSError as exc:
                self.logger.warning("Cannot create pdf_dir %s, defaulting to current directory" % user_request.pdf_dir)
                self.pdf_dir = "."
        
        self.output = user_request.output
        self.db_name = user_request.db_name
        self.pdf_type = user_request.pdf_type
        self.pdf_interval = user_request.pdf_interval
        self.plot_include = user_request.plot_include
        self.sigfigs = user_request.sigfigs
        self.sncl_format = user_request.sncl_format
        self.sds_files = user_request.sds_files

        self.netOrder = int(int(self.sncl_format.index("N"))/2)
        self.staOrder = int(int(self.sncl_format.index("S"))/2)
        self.locOrder = int(int(self.sncl_format.index("L"))/2)
        self.chanOrder = int(int(self.sncl_format.index("C"))/2)
 
        # Keep a /dev/null pipe handy in case we want to bit-dump output
        self.dev_null = open(os.devnull,"w")
        
        # add alias of EARTHSCOPE for IRIS
        if user_request.dataselect_url.upper() == "EARTHSCOPE":
            user_request.dataselect_url = "IRIS"
        if user_request.station_url is not None:
            if user_request.station_url.upper() == "EARTHSCOPE":
                user_request.station_url = "IRIS"
        if user_request.event_url is not None:
            if (user_request.event_url == "IRIS" or user_request.event_url.upper() == "EARTHSCOPE"):
                user_request.event_url = "USGS"
            
        ## Add dataselect clients and URLs or reference a local file
        self.dataselect_type = None
        if user_request.dataselect_url in URL_MAPPINGS.keys():
            # Get data from FDSN dataselect service
            self.dataselect_url = URL_MAPPINGS[user_request.dataselect_url]
            self.dataselect_type = "fdsnws"

            if user_request.dataselect_url == "IRISPH5":
                self.dataselect_type = "ph5ws"

            try:
                self.dataselect_client = Client(user_request.dataselect_url)
            except Exception as e:
                err_msg = e
                self.logger.critical(err_msg)
                raise SystemExit

            if user_request.station_url is not None:
               if user_request.station_url != user_request.dataselect_url:
                   self.logger.warning("Station_url should be the same as dataselect_url when retrieving data from FDSN or PH5 web services. Station_url '%s' does not match dataselect_url '%s'")

        elif "http://" in user_request.dataselect_url or "https://" in user_request.dataselect_url:
            self.dataselect_url = user_request.dataselect_url
            self.dataselect_type = "fdsnws"
            try:
                self.dataselect_client = Client(self.dataselect_url)
            except Exception as e:
                err_msg = e
                self.logger.critical(err_msg)
                raise SystemExit

            if user_request.station_url is not None:
                if user_request.station_url != user_request.dataselect_url:
                    self.logger.warning("Station_url should be the same as dataselect_url when retrieving data from FDSN webservices. Station_url '%s' does not match dataselect_url '%s'" 
                                         % (user_request.station_url, user_request.dataselect_url))

        else:
            if os.path.exists(os.path.abspath(user_request.dataselect_url)):
                # Get data from local miniseed files
                self.dataselect_url = os.path.abspath(user_request.dataselect_url)
                self.dataselect_client = None
            else:
                err_msg = "Cannot find dataselect_url: '%s'" % user_request.dataselect_url
                self.logger.critical(err_msg)
                raise SystemExit

        ## Add station clients and URLs or reference a local file
        if user_request.station_url is None:
            if ("http://" in self.dataselect_url or "https://" in self.dataselect_url):
                self.station_url = self.dataselect_url
                self.station_type = self.dataselect_type
                self.logger.info("Using station_url = %s" % self.dataselect_url)

                try:
                    self.station_client = Client(self.station_url)
                except Exception as e:
                    self.logger.warning(e)
                    self.logger.info("Metrics that require metadata information cannot be calculated")
                    self.station_url = None
                    self.station_client = None
            else:
                self.logger.info("No station_url found")
                self.logger.info("Metrics that require metadata information cannot be calculated")
                self.station_url = None
                self.station_client = None
        elif user_request.station_url in URL_MAPPINGS.keys():
            self.station_url = URL_MAPPINGS[user_request.station_url]
            self.station_type = "fdsnws"
            
            if user_request.station_url == "IRISPH5":
                self.station_type = "ph5ws"

            try:
                self.station_client = Client(user_request.station_url)
            except Exception as e:
                self.logger.warning(e)
                self.logger.info("Metrics that require metadata information cannot be calculated")
                self.station_url = None
                self.station_client = None
         
        elif "http://" in user_request.station_url or "https://" in user_request.station_url:
            self.station_url = user_request.station_url
            try:
                self.station_client = Client(self.station_url)
            except Exception as e:
                self.logger.warning(e)
                self.logger.info("Metrics that require metadata information cannot be calculated")
                self.station_url = None
                self.station_client = None
        else:
            if os.path.exists(os.path.abspath(user_request.station_url)):
                # Get data from local StationXML files
                self.station_url = os.path.abspath(user_request.station_url)
                self.station_client = None
            else:
                err_msg = "Cannot find station_url '%s'" % user_request.station_url
                self.logger.warning("Cannot find station_url '%s'" % user_request.station_url)
                self.logger.info("Metrics that require metadata information cannot be calculated")
                self.station_url = None
                self.station_client = None

        # Add event clients and URLs or reference a local file
        event_metrics = ["sample_snr","cross_talk","polarity_check","orientation_check"]
        if user_request.event_url is None:
            if any(map(lambda x: x in self.metric_names, event_metrics)):  # only warn if calculating event metrics
                self.logger.warning("event_url is None or not specified")
                self.logger.info("Metrics that require event information cannot be calculated")
            self.event_url = None  # no event service or xml, some metrics cannot be run
            self.event_client = None
        elif user_request.event_url == "USGS":
            self.event_url = "https://earthquake.usgs.gov"
            try:
               self.event_client = Client(self.event_url)
            except Exception as e:
               if any(map(lambda x: x in self.metric_names, event_metrics)):  # only warn if calculating event metrics 
                   self.logger.warning(e)
                   self.logger.info("Metrics that require event information cannot be calculated")
               self.event_url = None
               self.event_client = None
        elif user_request.event_url in URL_MAPPINGS.keys():
            self.event_url = URL_MAPPINGS[user_request.event_url]
            try:
                self.event_client = Client(self.event_url)
            except Exception as e:
                if any(map(lambda x: x in self.metric_names, event_metrics)):  # only warn if calculating event metrics
                    self.logger.warning(e)
                    self.logger.info("Metrics that require event information cannot be calculated")
                self.event_url = None
                self.event_client = None
        elif "http://" in user_request.event_url or "https://" in user_request.event_url:
            self.event_url = user_request.event_url
            try:
                self.event_client = Client(self.event_url)
            except Exception as e:
                if any(map(lambda x: x in self.metric_names, event_metrics)):  # only warn if calculating event metrics
                    self.logger.warning(e)
                    self.logger.info("Metrics that require event information cannot be calculated")
                self.event_url = None
                self.event_client = None
        else:
            if os.path.exists(os.path.abspath(user_request.event_url)):
                # Get data from local QUAKEML files
                self.event_url = os.path.abspath(user_request.event_url)
                self.event_client = None
            else:
                if any(map(lambda x: x in self.metric_names, event_metrics)):  # only warn if calculating event metrics
                    self.logger.warning("Cannot find event_url '%s'" % user_request.event_url)
                    self.logger.warning("Metrics that require event information cannot be calculated")
                self.event_url = None
                self.event_client = None

        # Deal with potential start = None
        if self.requested_starttime is None and self.dataselect_client is None:
            if self.requested_endtime is None:
               self.logger.info("No start or end time requested. Start and end time will be determined from local data file extents")
            else:
               self.logger.info("No start time requested. Start time will be determined from local data file extents")
            self.fileDates = []
            for sncl_pattern in self.sncl_patterns:
                matching_files = []
                if(self.sds_files):
                    fpattern1 = '%s' % (sncl_pattern + '.D' +  '.[12][0-9][0-9][0-9].[0-9][0-9][0-9]') #seiscomp sds file naming, waveform type D
                else:
                    fpattern1 = '%s' % (sncl_pattern + '.[12][0-9][0-9][0-9].[0-9][0-9][0-9]')
                fpattern2 = '%s' % (fpattern1 + '.[A-Z]')
                for root, dirnames, fnames in os.walk(self.dataselect_url):
                    for fname in fnmatch.filter(fnames, fpattern1) + fnmatch.filter(fnames, fpattern2):
                        matching_files.append(os.path.join(root,fname))
                if (len(matching_files) == 0):
                    continue
                else:
                    #self.logger.debug("Found files: \n %s" % '\n '.join(matching_files))
                    for _file in matching_files:
                        try:
                            _fileSNCL = _file.split("/")[-1]
                            if(self.sds_files):
                                _fileYear = _fileSNCL.split(".")[5]
                                _fileJday = _fileSNCL.split(".")[6]
                            else:
                                _fileYear = _fileSNCL.split(".")[4]
                                _fileJday = _fileSNCL.split(".")[5]
                            _fileDate = UTCDateTime("-".join([_fileYear,_fileJday]))
                            self.fileDates.append([_fileDate])
                        except Exception as e:
                            self.logger.debug(e)
                            self.logger.debug("Can't extract date from %s, %s" % (_file,e))
                            continue
            if (len(self.fileDates) == 0):
                self.logger.critical("No start date could be determined. No files found")
                raise SystemExit
            else:
                self.requested_starttime = min(self.fileDates)[0]
                if self.requested_endtime is None:
                    self.requested_endtime = max(self.fileDates)[0] +86400  # add one day
                self.logger.info("Start time %s" % self.requested_starttime.strftime("%Y-%m-%dT%H:%M:%S"))
                self.logger.info("End time %s" % self.requested_endtime.strftime("%Y-%m-%dT%H:%M:%S"))
        elif self.requested_starttime is None:
             self.logger.critical("--starttime must be specified for dataselect_url %s" % self.station_url)
             raise SystemExit
          

        # Output information
        filename_metrics = ''
        if len(self.user_request.requested_metric_set.split(',')) > 1:
            for metric in sorted(self.user_request.requested_metric_set.split(',')):
                if metric != 'pdf' and metric != 'psd_corrected':
                    filename_metrics = filename_metrics + metric + '-'
            filename_metrics =  filename_metrics[:-1]
        else:
            filename_metrics = self.user_request.requested_metric_set
        
        file_base = '%s_%s_%s_' % (filename_metrics,
                                  self.user_request.requested_sncl_set,
                                  self.requested_starttime.date)

        file_base = file_base.replace("*","x")
        file_base = file_base.replace("?","x")

        inclusiveEndtime = self.requested_endtime-1
        if(inclusiveEndtime.date != self.requested_starttime.date):
            file_base = file_base + '%s' % (inclusiveEndtime.date)
        else:
            file_base = file_base[:-1]

        self.output_file_base = self.csv_dir + '/' + file_base
        # Availability dataframe is stored if it is read from a local file
        self.availability = None
        self.initial_availability = None

        # Filtered availability dataframe is stored for potential reuse
        self.filtered_availability = None

        # Add local response files if used
        if user_request.resp_dir is None:                  # use irisws/evalresp
            self.resp_dir = None                           # use irisws/evalresp
        elif user_request.resp_dir in URL_MAPPINGS.keys(): # use EarthScope evalresp web service
            self.resp_dir = None 
        else:
            if os.path.exists(os.path.abspath(user_request.resp_dir)):   
                self.resp_dir = os.path.abspath(user_request.resp_dir)  # directory where RESP files are located 
                                                                        # file pattern:  RESP.<NET>.<STA>.<LOC>.<CHA> or RESP.<STA>.<NET>.<LOC>.<CHA>
            else:
                err_msg = "Cannot find resp_dir: '%s'" % user_request.resp_dir
                self.logger.error(err_msg)
                raise ValueError

        self.logger.debug("starttime %s, endtime %s", self.requested_starttime.strftime("%Y-%m-%dT%H:%M:%S"), self.requested_endtime.strftime("%Y-%m-%dT%H:%M:%S"))
        self.logger.debug("metric_names %s", self.metric_names)
        self.logger.debug("sncl_patterns %s", self.sncl_patterns)
        self.logger.debug("dataselect_url %s", self.dataselect_url)
        self.logger.debug("station_url %s", self.station_url)
        self.logger.debug("event_url %s", self.event_url)
        self.logger.debug("resp_dir %s", self.resp_dir)
        self.logger.debug("output %s", self.output)
        self.logger.debug("db_name %s", self.db_name)
        self.logger.debug("csv_dir %s", self.csv_dir)
        self.logger.debug("pdf_dir %s", self.pdf_dir)
        self.logger.debug("psd_dir %s", self.psd_dir)
        self.logger.debug("pdf_type %s", self.pdf_type)
        self.logger.debug("pdf_interval %s", self.pdf_interval)
        self.logger.debug("plot_include %s", self.plot_include)
        self.logger.debug("sigfigs %s", self.sigfigs)
        self.logger.debug("sncl_format %s", self.sncl_format)

    def get_sncl_pattern(self, netIn, staIn, locIn, chanIn):  
        snclList = list()
        snclList.insert(self.netOrder, netIn)
        snclList.insert(self.staOrder, staIn)
        snclList.insert(self.locOrder, locIn)
        snclList.insert(self.chanOrder, chanIn)
       
        sncl_pattern = "%s.%s.%s.%s" % tuple(snclList)
        return(sncl_pattern)

    def get_availability(self, metric,
                         network=None, station=None, location=None, channel=None,
                         starttime=None, endtime=None, 
                         latitude=None, longitude=None, minradius=None, maxradius=None):
        """
        ################################################################################
        # getAvailability method returns a dataframe with information from the output
        # of the fdsn station web service with "format=text&level=channel".
        # With additional parameters, this webservice returns information on all
        # matching SNCLs that have available data.
        #
        # The fdsnws/station/availability web service will return space characters for location
        # codes that are SPACE SPACE.
        #
        #   https://service.earthscope.org/fdsnws/station/1/
        #
        # #Network | Station | Location | Channel | Latitude | Longitude | Elevation | Depth | Azimuth | Dip | Instrument | Scale | ScaleFreq | ScaleUnits | SampleRate | StartTime | EndTime
        # CU|ANWB|00|LHZ|17.66853|-61.78557|39.0|0.0|0.0|-90.0|Streckeisen STS-2 Standard-gain|2.43609E9|0.05|M/S|1.0|2010-02-10T18:35:00|2599-12-31T23:59:59
        #
        ################################################################################
        
        if (!isGeneric("getAvailability")) {
          setGeneric("getAvailability", function(obj, network, station, location, channel,
                                                 #starttime, endtime,includerestricted,
                                                 starttime, endtime, 
                                                 latitude, longitude, minradius, maxradius) {
            standardGeneric("getAvailability")
          })
        }
        
        # END of R documentation


        Returns a dataframe of SNCLs available from the `station_url` source
        specified in the `user_request` object used to initialize the
        `Concierge`.

        By default, information in the `user_request` is used to generate
        a FDSN webservices request for station data. Where arguments are
        provided, these are used to override the information found in
        `user_request`.

        :type network: str
        :param network: Select one or more network codes. Can be SEED network
            codes or data center defined codes. Multiple codes are
            comma-separated.
        :type station: str
        :param station: Select one or more SEED station codes. Multiple codes
            are comma-separated.
        :type location: str
        :param location: Select one or more SEED location identifiers. Multiple
            identifiers are comma-separated. As a special case ``"--"`` (two
            dashes) will be translated to a string of two space characters to
            match blank location IDs.
        :type channel: str
        :param channel: Select one or more SEED channel codes. Multiple codes
            are comma-separated.
        :type starttime: :class:`~obspy.core.utcdatetime.UTCDateTime`
        :param starttime: Limit to metadata epochs starting on or after the
            specified start time.
        :type endtime: :class:`~obspy.core.utcdatetime.UTCDateTime`
        :param endtime: Limit to metadata epochs ending on or before the
            specified end time.
        #:type includerestricted: bool
        #:param includerestricted: Specify if results should include information
        #    for restricted stations.
        :type latitude: float
        :param latitude: Specify the latitude to be used for a radius search.
        :type longitude: float
        :param longitude: Specify the longitude to the used for a radius
            search.
        :type minradius: float
        :param minradius: Limit results to stations within the specified
            minimum number of degrees from the geographic point defined by the
            latitude and longitude parameters.
        :type maxradius: float
        :param maxradius: Limit results to stations within the specified
            maximum number of degrees from the geographic point defined by the
            latitude and longitude parameters.

        #.. rubric:: Example

        #>>> my_request =  UserRequest(dummy=True)
        #>>> concierge = Concierge(my_request)
        #>>> concierge.get_availability() #doctest: +ELLIPSIS
        #[u'US.OXF..BHE', u'US.OXF..BHN', u'US.OXF..BHZ']
        """

        # NOTE:  Building the availability dataframe from a large StationXML is time consuming.
        # NOTE:  If we are using local station data then we should only do this once.
        
        # Special case when using all defaults helps speed up any metrics making mutiple calls to get_availability
        # NOTE: If future metrics require this, then uncomment here and add concierge.filtered_availability = None to the end of every metric script.
        #if (network is None and
        #    station is None and
        #    location is None and
        #    channel is None and
        #    starttime is None and
        #    endtime is None and
        #    self.filtered_availability is not None):
        #    return(self.filtered_availability)
        
        # Read from a local StationXML file one time only -- IE, once this section has been run once in a job, don't run it again... so availability2 wont run this section.
        if self.station_client is None:
            # Using Local Data        

            # Only read/parse if we haven't already done so

            if self.initial_availability is None:
                try:
                    # Get list of all sncls we have metadata for
                    if self.station_url is not None:            
                        self.logger.info("Reading StationXML file %s" % self.station_url)
                        sncl_inventory = obspy.read_inventory(self.station_url, format="STATIONXML")
                        
                except Exception as e:
                    err_msg = "The StationXML file: '%s' is not valid" % self.station_url
                    self.logger.debug(e)
                    self.logger.error(err_msg)   
                    raise ValueError
                
                self.logger.debug('Building availability dataframe...')

                # Allow arguments to override UserRequest parameters
                if starttime is None:
                    _starttime = self.requested_starttime
                else:
                    _starttime = starttime
                if endtime is None:
                    _endtime = self.requested_endtime
                else:
                    _endtime = endtime
                
                # Set up empty dataframe
                df = pd.DataFrame(columns=("network", "station", "location", "channel",
                                           "latitude", "longitude", "elevation", "depth" ,
                                           "azimuth", "dip", "instrument",
                                           "scale", "scalefreq", "scaleunits", "samplerate",
                                           "starttime", "endtime", "snclId"), dtype="object")


                # Walk through the Inventory object and fill the dataframe with metadata
                if 'sncl_inventory' in locals():
                    for n in sncl_inventory.networks:
                        for s in n.stations:
                            for c in s.channels:
                                if (c.start_date < _endtime) and ((c.end_date > _starttime) or (c.end_date is None)):
                                    if c.end_date is None:
                                        tmpend = UTCDateTime("2599-12-31T23:59:59")
                                    else:
                                        tmpend = c.end_date
                                    snclId = self.get_sncl_pattern(n.code, s.code, c.location_code, c.code)
                                    if c.response.instrument_sensitivity is None:
                                        df.loc[len(df)] = [n.code, s.code, c.location_code, c.code,
                                                          c.latitude, c.longitude, c.elevation, c.depth,
                                                          c.azimuth, c.dip, c.sensor.description,
                                                          None,
                                                          None,
                                                          None,
                                                          c.sample_rate,
                                                          c.start_date, c.end_date, snclId]
                                    else:
                                        df.loc[len(df)] = [n.code, s.code, c.location_code, c.code,
                                                          c.latitude, c.longitude, c.elevation, c.depth,
                                                          c.azimuth, c.dip, c.sensor.description,
                                                          c.response.instrument_sensitivity.value,
                                                          c.response.instrument_sensitivity.frequency,
                                                          c.response.instrument_sensitivity.input_units,
                                                          c.sample_rate,
                                                          c.start_date, c.end_date, snclId]
                            
                # Add local data to the dataframe, even if we don't have metadata
                # Loop through all sncl_patterns in the preferences file ---------------
                self.logger.debug("Searching for data in %s" % self.dataselect_url)

                for sncl_pattern in self.sncl_patterns:
                    try: 
                        UR_network = sncl_pattern.split('.')[self.netOrder]
                        UR_station = sncl_pattern.split('.')[self.staOrder]
                        UR_location = sncl_pattern.split('.')[self.locOrder]
                        UR_channel = sncl_pattern.split('.')[self.chanOrder]
                        
                    except Exception as e:
                        err_msg = "Could not parse sncl_pattern %s" % (sncl_pattern)
                        self.logger.error(err_msg)
                        raise ValueError

                    # Allow arguments to override UserRequest parameters
                    if network is None:
                        _network = UR_network
                    else:
                        _network = network
                    if station is None:
                        _station = UR_station
                    else:
                        _station = station
                    if location is None:
                        _location = UR_location
                    else:
                        _location = location
                    if channel is None:
                        _channel = UR_channel
                    else:
                        _channel = channel

                    _sncl_pattern = self.get_sncl_pattern(_network,_station,_location,_channel)
                    self.logger.debug("Adding %s to availability dataframe" % _sncl_pattern)

                    if (self.station_client is None):	# Local metadata
                        if self.dataselect_client is None:	# Local data
                            # Loop over the available data and add to dataframe if they aren't yet
                            # But only for the requested days 
                            if (len(sncl_pattern.split('.')) > 4): #expected to be quality code
                                tmp_sncl_pattern = os.path.splitext(sncl_pattern)[0]
                                q = os.path.splitext(sncl_pattern)[1][1]

                                if(self.sds_files):
                                    fpattern1 = '%s' % (tmp_sncl_pattern + '.D' + '.[12][0-9][0-9][0-9].[0-9][0-9][0-9]') #SDS file naming structure, D=waveform data
                                else:
                                    fpattern1 = '%s' % (tmp_sncl_pattern + '.[12][0-9][0-9][0-9].[0-9][0-9][0-9]')

                                if q.isalpha():
                                    fpattern2 = '%s' % (fpattern1 + '.' + q)
                                else:
                                    fpattern2 = '%s' % (fpattern1 + '.[A-Z]')

                            else:
                                if(self.sds_files):
                                    fpattern1 = '%s' % (sncl_pattern + '.D' + '.[12][0-9][0-9][0-9].[0-9][0-9][0-9]')
                                else:
                                    fpattern1 = '%s' % (sncl_pattern + '.[12][0-9][0-9][0-9].[0-9][0-9][0-9]')
                                fpattern2 = '%s' % (fpattern1 + '.[A-Z]')

                            matching_files = []

                            for root, dirnames, fnames in os.walk(self.dataselect_url):
                                for fname in fnmatch.filter(fnames, fpattern1) + fnmatch.filter(fnames, fpattern2):
                                    if(self.sds_files):
                                        position5 = fname.split('.')[5]
                                        position6 = fname.split('.')[6]
                                        if(fnmatch.fnmatch(position5,'[12][0-9][0-9][0-9]') and fnmatch.fnmatch(position6,'[0-9][0-9][0-9]')):
                                            file_year = int(position5)
                                            file_day = int(position6)
                                        else:
                                            continue
                                    else:
                                        position4 = fname.split('.')[4]
                                        position5 = fname.split('.')[5]
                                        if(fnmatch.fnmatch(position4,'[12][0-9][0-9][0-9]') and fnmatch.fnmatch(position5,'[0-9][0-9][0-9]')):
                                            file_year = int(position4)
                                            file_day = int(position5)
                                        else:
                                            continue
                                    file_date = (datetime.datetime(file_year, 1, 1) + datetime.timedelta(file_day - 1)).date()
                                    
                                    # Compare the date on the file to the dates of the start and end time (but not the 
                                    # actual start and end time, since that can be a partial day)
                                    if file_date >= _starttime.date and file_date < _endtime:
                                        matching_files.append(os.path.join(root,fname))

                            
                            if (len(matching_files) == 0):
                                continue
                            else:
                                # Loop over all files that we have matching our desired sncls
                                for _file in matching_files:
                                    fileSNCL = _file.split("/")[-1]
                                    snclId = fileSNCL.split(".")[0] + "." + fileSNCL.split(".")[1] + "." + fileSNCL.split(".")[2] + "." + fileSNCL.split(".")[3] 
                                    if not any(df.snclId.str.contains(snclId)):	
                                        # Only add if not already in the df
                                        df.loc[len(df)] = [fileSNCL.split(".")[self.netOrder], fileSNCL.split(".")[self.staOrder], 
                                                           fileSNCL.split(".")[self.locOrder], fileSNCL.split(".")[self.chanOrder],
                                                           None, None, None, None,
                                                           None, None, None,
                                                           None, None, None,
                                                           None, UTCDateTime("1900-01-01"), UTCDateTime("2599-12-31"),
                                                           snclId]

                # Now save the dataframe internally
                self.initial_availability = df

        # Container for all of the individual sncl_pattern dataframes generated
        sncl_pattern_dataframes = []
        loopCounter = 0		# For crossCorrelation when we look for all sn.ls

        # Loop through all sncl_patterns ---------------------------------------
        for sncl_pattern in self.sncl_patterns:
            # We only want to do this one time if we are looking for *.*.*.chan
            # For example, during crossCorrelation.  Otherwise it creates a bloated
            # availability dataframe with the same sncls repeating #sncl_patterns times
            loopCounter += 1
            if (network == "*" and station == "*" and location == "*" and loopCounter > 1):
                continue

            # Get "User Request" parameters
            try: 
                UR_network = sncl_pattern.split('.')[self.netOrder]
                UR_station = sncl_pattern.split('.')[self.staOrder]
                UR_location = sncl_pattern.split('.')[self.locOrder]
                UR_channel = sncl_pattern.split('.')[self.chanOrder]
            except Exception as e:
                err_msg = "Could not parse sncl_pattern %s" % (sncl_pattern)
                self.logger.error(err_msg)
                raise ValueError

            # Allow arguments to override UserRequest parameters
            if starttime is None:
                _starttime = self.requested_starttime
            else:
                _starttime = starttime
            if endtime is None:
                _endtime = self.requested_endtime
            else:
                _endtime = endtime
            if network is None:
                _network = UR_network
            else:
                _network = network
            if station is None:
                _station = UR_station
            else:
                _station = station
            if location is None:
                _location = UR_location
            else:
                _location = location
            if channel is None:
                _channel = UR_channel
            else:
                _channel = channel
                
            
            
            _sncl_pattern = self.get_sncl_pattern(_network, _station, _location, _channel)

            
            # Get availability dataframe ---------------------------------------
            if self.station_client is None:
                # Use pre-existing internal dataframe if we are using local data, filtered by time 
                
                df = self.initial_availability
               
                for ind, row in df.iterrows():
                    if not (row['endtime'] is None):
                        if  not (row['starttime'] < _endtime-1) & (row['endtime'] > _starttime):
                            df.drop([ind], inplace=True)
                    else:
                        if not row['starttime'] < _endtime-1:
                            df.drop([ind], inplace=True)
#                         df = df[(df['starttime'] < _endtime-1)]
                        
                if df is None:
                    continue 
            elif self.station_type == "ph5ws":
                self.logger.debug("read IRISPH5 station web services %s/%s for %s,%s,%s,%s,%s,%s" % (self.station_url,self.station_type,_network, _station, _location, _channel, _starttime.strftime('%Y.%j'), _endtime.strftime('%Y.%j')))
                try:
                    df = irisseismic.getAvailability(self.station_url,self.station_type,network=_network, station=_station,
                                                     location=_location, channel=_channel,starttime=_starttime, endtime=_endtime,
                                                     includerestricted=True,
                                                     latitude=latitude, longitude=longitude, minradius=minradius, maxradius=maxradius)
                                                     
                except Exception as e:
                    if (minradius):
                        err_msg = "No stations found for %s within radius %s-%s degrees of latitude,longitude %s,%s" % (_sncl_pattern,minradius,maxradius,latitude,longitude)
                    else:
                        err_msg = "No stations found for %s" % (_sncl_pattern)
                    self.logger.debug(str(e).strip('\n'))
                    self.logger.info(err_msg)
                    continue

                if (df.empty):
                    if (minradius):
                        err_msg = "No stations found for %s within radius %s-%s degrees of latitude,longitude %s,%s" % (_sncl_pattern,minradius,maxradius,latitude,longitude)
                    else:
                        err_msg = "No stations found for %s" % (_sncl_pattern)
                    self.logger.info(err_msg)
                    continue

                self.logger.debug('Adding %s to the availability dataframe' % _sncl_pattern)

            else:
                # Read from FDSN web services
                self.logger.debug("read FDSN station web services %s for %s,%s,%s,%s,%s,%s" % (self.station_url,_network, _station, _location, _channel, _starttime.strftime('%Y.%j'), _endtime.strftime('%Y.%j')))
                try:
                    sncl_inventory = self.station_client.get_stations(starttime=_starttime, endtime=_endtime,
                                                                      network=_network, station=_station,
                                                                      location=_location, channel=_channel,
                                                                      includerestricted=True,
                                                                      latitude=latitude, longitude=longitude,
                                                                      minradius=minradius, maxradius=maxradius,                                                                
                                                                      level="channel")
                    
                except Exception as e:
                    if (re.match('The parameter \'includerestricted\' is not supported by the service.',str(e))):
                        try:
                            sncl_inventory = self.station_client.get_stations(starttime=_starttime, endtime=_endtime,
                                                                      network=_network, station=_station,
                                                                      location=_location, channel=_channel,
                                                                      latitude=latitude, longitude=longitude,
                                                                      minradius=minradius, maxradius=maxradius,
                                                                      level="channel")
                        except Exception as e:
                            if (minradius):
                                err_msg = "No stations found for %s within radius %s-%s degrees of latitude,longitude %s,%s" % (_sncl_pattern,minradius,maxradius,latitude,longitude)
                            else:
                                err_msg = "No stations found for %s" % (_sncl_pattern)
                            self.logger.debug(str(e).strip('\n'))
                            self.logger.info(err_msg)
                            continue
                    elif (minradius):
                        err_msg = "No stations found for %s within radius %s-%s degrees of latitude,longitude %s,%s" % (_sncl_pattern,minradius,maxradius,latitude,longitude)
                        self.logger.debug(str(e).strip('\n'))
                        self.logger.info(err_msg)
                        continue
                    else:
                        err_msg = "No stations found for %s" % (_sncl_pattern)
                        self.logger.debug(str(e).strip('\n'))
                        self.logger.info(err_msg)
                        continue

                self.logger.debug('Adding %s to the availability dataframe' % _sncl_pattern)

                # Set up empty dataframe
                df = pd.DataFrame(columns=("network", "station", "location", "channel",
                                           "latitude", "longitude", "elevation", "depth" ,
                                           "azimuth", "dip", "instrument",
                                           "scale", "scalefreq", "scaleunits", "samplerate",
                                           "starttime", "endtime", "snclId"), dtype="object")

                # Walk through the Inventory object
                for n in sncl_inventory.networks:
                    for s in n.stations:
                        for c in s.channels:
                            snclId = self.get_sncl_pattern(n.code, s.code, c.location_code, c.code)
                            if c.response.instrument_sensitivity is None:
                                df.loc[len(df)] = [n.code, s.code, c.location_code, c.code,
                                               c.latitude, c.longitude, c.elevation, c.depth,
                                               c.azimuth, c.dip, c.sensor.description,
                                               None,
                                               None,
                                               None,
                                               c.sample_rate,
                                               c.start_date, c.end_date, snclId]
                            else:
                                df.loc[len(df)] = [n.code, s.code, c.location_code, c.code,
                                               c.latitude, c.longitude, c.elevation, c.depth,
                                               c.azimuth, c.dip, c.sensor.description,
                                               c.response.instrument_sensitivity.value,
                                               c.response.instrument_sensitivity.frequency,
                                               c.response.instrument_sensitivity.input_units,
                                               c.sample_rate,
                                               c.start_date, c.end_date, snclId]


            # Subset availability dataframe based on _sncl_pattern -------------

            # NOTE:  This shouldn't be necessary for dataframes obtained from FDSN
            # NOTE:  but it's quick so we always do it
            
            # Create python regex from _sncl_pattern
            # NOTE:  Replace '.' first before introducing '.*' or '.'!
            py_pattern = _sncl_pattern.replace('.','\\.').replace('*','.*').replace('?','.')

            
            # Filter dataframe
            df = df[df.snclId.str.contains(py_pattern)]
            
                       
            # Subset based on locally available data ---------------------------
            if self.dataselect_client is None and metric != "simple":
                if(self.sds_files):
                    fpattern1 = '%s.D.%s' % (_sncl_pattern,_starttime.strftime('%Y.%j'))
                else:
                    fpattern1 = '%s.%s' % (_sncl_pattern,_starttime.strftime('%Y.%j'))
                fpattern2 = '%s' % (fpattern1 + '.[A-Z]')
                
                matching_files = []
                for root, dirnames, fnames in os.walk(self.dataselect_url):
                    for fname in fnmatch.filter(fnames, fpattern1) + fnmatch.filter(fnames, fpattern2):
                        if(self.sds_files):
                            position5 = fname.split('.')[5]
                            position6 = fname.split('.')[6]
                            if(fnmatch.fnmatch(position5,'[12][0-9][0-9][0-9]') and fnmatch.fnmatch(position6,'[0-9][0-9][0-9]')):
                                file_year = int(position5)
                                file_day = int(position6)
                            else:
                                continue
                        else:
                            position4 = fname.split('.')[4]
                            position5 = fname.split('.')[5]
                            if(fnmatch.fnmatch(position4,'[12][0-9][0-9][0-9]') and fnmatch.fnmatch(position5,'[0-9][0-9][0-9]')):
                                file_year = int(position4)
                                file_day = int(position5)
                            else:
                                continue

                        file_date = (datetime.datetime(file_year, 1, 1) + datetime.timedelta(file_day - 1)).date()
                        
                        # Compare the date on the file to the dates of the start and end time (but not the 
                        # actual start and end time, since that can be a partial day)
                        if file_date >= _starttime.date and file_date < _endtime:
                            matching_files.append(os.path.join(root,fname))
                        
                        
                        
                        
#                         matching_files.append(os.path.join(root,fname))
                if (len(matching_files) == 0):
                    err_msg = "No local waveforms matching %s" % fpattern1
                    self.logger.debug(err_msg)
                    continue
                else:
                    # Create a mask based on available file names
                    mask = df.snclId.str.contains("MASK WITH ALL FALSE")
 
                    for i in range(len(matching_files)):
                        basename = os.path.basename(matching_files[i])
                        match = re.match('[^\\.]*\\.[^\\.]*\\.[^\\.]*\\.[^\\.]*',basename)
                        sncl = match.group(0)
                        py_pattern = sncl.replace('.','\\.')
                        mask = mask | df.snclId.str.contains(py_pattern)
                         
                # Subset based on the mask
                df = df[mask]

            # Subset based on distance
            # Create a temporary column that has the distances, use to subset
            df.insert(0,'dist',"EMPTY")
            if maxradius is not None or minradius is not None:
                # There are distance constraints
                for ii in range(len(df)):
                    lat = df['latitude'].iloc[ii]; 
                    lon = df['longitude'].iloc[ii]; 
                    if (lat and lon):
                        if not (math.isnan(lon) or math.isnan(lat)):
                            [dist,AB,BA] = obspy.geodetics.base.gps2dist_azimuth(latitude, longitude, lat, lon)
                            dist = obspy.geodetics.base.kilometer2degrees(dist/1000)
                            if (minradius is None) and (maxradius is not None):
                                if abs(dist) <= maxradius:
                                    df["dist"].iloc[ii] = "KEEP"
                            elif (maxradius is None) and (minradius is not None):
                                if abs(dist) >= minradius:
                                    df["dist"].iloc[ii] = "KEEP"
                            elif (maxradius is not None) and (minradius is not None):
                                if abs(dist) <= maxradius and  abs(dist) >= minradius:
                                    df["dist"].iloc[ii] = "KEEP"
                        else:
                            next
                    else:
                        next
                df = df[df.dist.str.contains("KEEP")]
            df = df.drop('dist', 1)
            

            # Append this dataframe
            if df.shape[0] == 0:
                self.logger.debug("No SNCLS found matching '%s' (sncl_format=%s)" % (_sncl_pattern,self.sncl_format))
            else:
                #if df.snclId not in sncl_pattern_dataframes[:].snclId:
                sncl_pattern_dataframes.append(df)	# tack the dataframes together
        # END of sncl_patterns loop --------------------------------------------
 
        if len(sncl_pattern_dataframes) == 0:
            err_msg = "No available waveforms for %s matching " % _starttime.strftime('%Y-%m-%d') + str(self.sncl_patterns)
            self.logger.info(err_msg)
#             return pd.DataFrame()
            return None
            #raise NoAvailableDataError(err_msg)
        else:
            # Those dataframes become availability
            availability = pd.concat(sncl_pattern_dataframes, ignore_index=True, verify_integrity=True)

            # Remove duplicates -- starttime/endtime datatypes don't allow drop_duplicates
            # convert starttime to string in new column ("start"), drop_duplicates using that, remove column
            availability['start'] = availability['starttime'].astype('str')
            availability = availability.drop_duplicates(['snclId', 'start'])
            availability = availability.drop('start', 1)

            if availability.shape[0] == 0:              
                err_msg = "No available waveforms matching" + str(self.sncl_patterns)
                self.logger.info(err_msg)
                return pd.DataFrame()
            else:
                # The concierge should remember this dataframe for metrics that
                # make multiple calls to get_availability with all defaults.
                self.filtered_availability = availability
                return availability

    def get_dataselect(self,
                       network=None, station=None, location=None, channel=None,
                       starttime=None, endtime=None, quality=None, repository=None,
                       inclusiveEnd=False, ignoreEpoch=False):
        """
        Returns an R Stream that can be passed to metrics calculation methods.

        All arguments are required except for starttime and endtime. These arguments
        may be specified but will default to the time information found in the
        `user_request` used to generate a FDSN webservices request for MINIseed data.

        :type network: str
        :param network: Select one or more network codes. Can be SEED network
            codes or data center defined codes. Multiple codes are
            comma-separated.
        :type station: str
        :param station: Select one or more SEED station codes. Multiple codes
            are comma-separated.
        :type location: str
        :param location: Select one or more SEED location identifiers. Multiple
            identifiers are comma-separated. As a special case ``"--"`` (two
            dashes) will be translated to a string of two space characters to
            match blank location IDs.
        :type channel: str
        :param channel: Select one or more SEED channel codes. Multiple codes
            are comma-separated.
        :type starttime: :class:`~obspy.core.utcdatetime.UTCDateTime`
        :param starttime: Limit to metadata epochs starting on or after the
            specified start time.
        :type endtime: :class:`~obspy.core.utcdatetime.UTCDateTime`
        :param endtime: Limit to metadata epochs ending on or before the
            specified end time.
        """

        # Allow arguments to override UserRequest parameters
        if starttime is None:
            _starttime = self.requested_starttime
        else:
            _starttime = starttime
        if endtime is None:
            _endtime = self.requested_endtime
        else:
            _endtime = endtime

        if self.dataselect_type is None:
            # Read local MiniSEED file and convert to R_Stream
            nday = int((_endtime - .00001).julday - _starttime.julday) + 1   # subtract a short amount of time for 00:00:00 endtimes
            
            if (nday == 1):
                _sncl_pattern = self.get_sncl_pattern(network, station, location, channel)
                if(self.sds_files):
                    fpattern1 = '%s.D.%s' % (_sncl_pattern,_starttime.strftime('%Y.%j'))  #seiscomp sds file naming
                else:
                    fpattern1 = '%s.%s' % (_sncl_pattern,_starttime.strftime('%Y.%j'))
                fpattern2 = '%s' % (fpattern1 + '.[A-Z]')
                
                matching_files = []
                for root, dirnames, fnames in os.walk(self.dataselect_url):
                    for fname in fnmatch.filter(fnames, fpattern1) + fnmatch.filter(fnames, fpattern2):
                        matching_files.append(os.path.join(root,fname))

                try:
                    # Get the ObsPy version of the stream

                    if (len(matching_files) == 0):
                        self.logger.info("No files found matching '%s'" % (fpattern1))
                        py_stream = obspy.read().clear()
                        act_flags = []
                        io_flags = []
                        dq_flags = []
                        timing_qual=None
                    
                    else:
                        filepath=matching_files[0]
                        
                        if (len(matching_files) > 1):
                            self.logger.debug("Multiple files found: %s" % " ".join(matching_files))
                            self.logger.warning("Multiple files found matching " '%s -- using %s' % (fpattern1, filepath))
                        
                        if not inclusiveEnd:
                            _endtime = _endtime - 0.000001
                            
                        self.logger.debug("read local miniseed file for %s..." % filepath)
                        py_stream = obspy.read(filepath).sort()

                        py_stream = py_stream.slice(_starttime, _endtime, nearest_sample=False)
                      
                        if (StrictVersion(obspy.__version__) < StrictVersion("1.1.0")): 
                            flag_dict = obspy.io.mseed.util.get_timing_and_data_quality(filepath)
                            act_flags = [0,0,0,0,0,0,0,0] # not supported before 1.1.0  
                            io_flags = [0,0,0,0,0,0,0,0]  # not supported before 1.1.0
                            dq_flags = flag_dict['data_quality_flags']
                        else:
                            flag_dict = obspy.io.mseed.util.get_flags(filepath)
                            act_flags = []
                            io_flags = []
                            dq_flags = []
                            for k,v in flag_dict['activity_flags_counts'].items():
                                act_flags.append(v) 
                            for k,v in flag_dict['io_and_clock_flags_counts'].items():
                                io_flags.append(v)
                            for k,v in flag_dict['data_quality_flags_counts'].items():
                                dq_flags.append(v)
                            
                        if flag_dict["timing_quality"]:
                            timing_qual=flag_dict["timing_quality"]["mean"]
                        else:
                            timing_qual=None
                            
                    # NOTE:  ObsPy does not store station metadata with each trace.
                    # NOTE:  We need to read them in separately from station metadata.
                    availability = self.get_availability("dummy", network, station, location, channel, _starttime, _endtime)
                    
                    if availability is None:
                        raise Exception('No Data')
                        return None
 
                    if(ignoreEpoch == False):
                        if (len(availability) > 1):
                            raise Exception("Multiple metadata epochs found for %s" % _sncl_pattern)

                    
                    sensor = availability.instrument[0]
                    scale = availability.scale[0]
                    scalefreq = availability.scalefreq[0]
                    scaleunits = availability.scaleunits[0]
                    if sensor is None: sensor = ""          
                    if scale is None: scale = np.NaN            
                    if scalefreq is None: scalefreq = np.NaN    
                    if scaleunits is None: scaleunits = ""  
                    latitude = availability.latitude[0]
                    longitude = availability.longitude[0]
                    elevation = availability.elevation[0]
                    depth = availability.depth[0]
                    azimuth = availability.azimuth[0]
                    dip = availability.dip[0]
                        
                    # Create the IRISSeismic version of the stream
                    r_stream = irisseismic.R_Stream(py_stream, _starttime, _endtime, act_flags, io_flags, dq_flags, timing_qual,
						sensor, scale, scalefreq, scaleunits, latitude, longitude, elevation, depth, azimuth, dip)

                except Exception as e:
                    self.logger.debug(e)
                    raise
      
#                 # Create the IRISSeismic version of the stream -- is this second call necessary? Uncomment if things start misbehaving.
#                 r_stream = irisseismic.R_Stream(py_stream, _starttime, _endtime, act_flags, io_flags, dq_flags, timing_qual,
#                     sensor, scale, scalefreq, scaleunits, latitude, longitude, elevation, depth, azimuth, dip)
                   
#                 if len(utils.get_slot(r_stream, 'traces')) == 0:
#                     raise Exception("no data available") 


            else:
                # create tempfile
                x = tempfile.TemporaryFile()

                # begin day loop
                for day in range(nday):
                    start = (_starttime + day * 86400)
                    start = start - (start.hour * 3600 + start.minute * 60 + start.second + start.microsecond * .000001)
                    end = start + 86400

                    if start <= _starttime:
                        start = _starttime
                    if end >= _endtime:
                        end = _endtime

                    _sncl_pattern = self.get_sncl_pattern(network, station, location, channel)

                    if(self.sds_files):
                        filename = '%s.D.%s' % (_sncl_pattern,start.strftime('%Y.%j'))  #seiscomp sds file naming
                    else:
                        filename = '%s.%s' % (_sncl_pattern,start.strftime('%Y.%j'))

                    self.logger.debug("read local miniseed file for %s..." % filename)
                    fpattern1 = self.dataselect_url + '/' + filename 
                    fpattern2 = fpattern1 + '.[A-Z]'
                    matching_files = glob.glob(fpattern1) + glob.glob(fpattern2)
		
                    if (len(matching_files) == 0):
                        err_msg = "No files found matching '%s'" % (fpattern1)
                        raise Exception(err_msg)
		    
                    else:
                        filepath = matching_files[0]
                        if (len(matching_files) > 1):
                            self.logger.debug("Multiple files found: %s" % " ".join(matching_files))
                            self.logger.warning("Multiple files found matching" '%s -- using %s' % (fpattern1, filepath))

                        # write miniseed to tempfile
                        with open(filepath, 'rb') as f:
                            x.write(f.read())
                            x.flush()
                        f.close()

                try:
                    py_stream = obspy.read(x).sort()
                    x.close()
                    if not inclusiveEnd:
                            _endtime = _endtime - 0.000001
                    py_stream = py_stream.slice(_starttime, _endtime, nearest_sample=False) 
                    # NOTE:  ObsPy does not store state-of-health flags with each stream.
                    if (StrictVersion(obspy.__version__) < StrictVersion("1.1.0")):
                        flag_dict = obspy.io.mseed.util.get_timing_and_data_quality(filepath)
                        act_flags = [0,0,0,0,0,0,0,0] 
                        io_flags = [0,0,0,0,0,0,0,0] 
                        dq_flags = flag_dict['data_quality_flags']
                    else:
                        flag_dict = obspy.io.mseed.util.get_flags(filepath)
                        act_flags = []
                        io_flags = []
                        dq_flags = []
                        for k,v in flag_dict['activity_flags_counts'].items():
                            act_flags.append(v)
                        for k,v in flag_dict['io_and_clock_flags_counts'].items():
                            io_flags.append(v)
                        for k,v in flag_dict['data_quality_flags_counts'].items():
                            dq_flags.append(v)

                    if flag_dict["timing_quality"]:
                        timing_qual=flag_dict["timing_quality"]["mean"]
                    else:
                        timing_qual=None

                    # NOTE:  ObsPy does not store station metadata with each trace.
                    # NOTE:  We need to read them in separately from station metadata.
                    # NOTE:  This should be consistent for each day of data
                    self.logger.info('%s, %s,%s,%s' % (network,station,location,channel))
                    availability = self.get_availability("dummy", network, station, location, channel, _starttime, _endtime)
                    
                    if availability is None:
                        return None
                    
                    if(ignoreEpoch == False):
                        if (len(availability) > 1):
                            raise Exception("Multiple metadata epochs found for %s" % _sncl_pattern)

                    sensor = availability.instrument[0]
                    scale = availability.scale[0]
                    scalefreq = availability.scalefreq[0]
                    scaleunits = availability.scaleunits[0]
                    if sensor is None: sensor = ""          
                    if scale is None: scale = np.NaN           
                    if scalefreq is None: scalefreq = np.NaN   
                    if scaleunits is None: scaleunits = ""  
                    latitude = availability.latitude[0]
                    longitude = availability.longitude[0]
                    elevation = availability.elevation[0]
                    depth = availability.depth[0]
                    azimuth = availability.azimuth[0]
                    dip = availability.dip[0]

                    # Create the IRISSeismic version of the stream
                    r_stream = irisseismic.R_Stream(py_stream, _starttime, _endtime, act_flags, io_flags, dq_flags, timing_qual,
						    sensor, scale, scalefreq, scaleunits, latitude, longitude, elevation, depth, azimuth, dip)
            
                except Exception as e:
                    err_msg = "Error reading in local waveform from %s" % filepath
                    self.logger.debug(e)
                    self.logger.debug(err_msg)
                    raise

#                 if len(utils.get_slot(r_stream, 'traces')) == 0:
#                         raise Exception("no data available")
            
            try:
                self.logger.debug(f"Dataselect found local data that spans {py_stream.traces[0].stats.starttime} - {py_stream.traces[-1].stats.endtime}")
            except:
                self.logger.debug("Dataselect found no local data")

        else:
            # Read from FDSN web services
            try:
                # R getDataselect() seems to capture awkward error reports when there is no data
                # we want to suppress the stderr channel briefly to block the unwanted feedback from R
                orig_stderr = sys.stderr
                sys.stderr = self.dev_null
                r_stream = irisseismic.R_getDataselect(self.dataselect_url, self.dataselect_type, network, station, location, channel, _starttime, _endtime, quality, repository,inclusiveEnd, ignoreEpoch)
                
                sys.stderr = orig_stderr
            except Exception as e:
                err_msg = "Error reading in waveform from %s dataselect webservice client (base url: %s)" % (self.dataselect_type, self.dataselect_url)
                self.logger.error(err_msg)
                self.logger.debug(str(e).strip('\n'))
                raise

            # Some FDSN web services cut on record boundaries instead of samples, so make sure we have correct start/end times
            try:
                r_stream = irisseismic.R_slice(r_stream,_starttime, _endtime)
                
                
            except Exception as e:
                err_msg = "Error cutting R stream for start %s and end %s" % (_starttime, _endtime)
                self.logger.debug(err_msg)
                raise


        # TODO:  Do we need to test for valid R_Stream.
        if False:              
            return None # TODO:  raise an exception
        else:
            return r_stream


    def get_event(self,
                  starttime=None, endtime=None,
                  minmag=5.5, maxmag=None, magtype=None,
                  mindepth=None, maxdepth=None):
        """
        ################################################################################
        # getEvent method returns seismic event data from the event webservice:
        #
        #   https://earthquake.usgs.gov/fdsnws/event/1/
        #
        # TODO:  The getEvent method could be fleshed out with a more complete list
        # TODO:  of arguments to be used as ws-event parameters.
        ################################################################################
        
        # https:/earthquake.usgs.gov/fdsnws/event/1/query?starttime=2013-02-01T00:00:00&endtime=2013-02-02T00:00:00&minmag=5&format=text
        #
        # #EventID | Time | Latitude | Longitude | Depth | Author | Catalog | Contributor | ContributorID | MagType | Magnitude | MagAuthor | EventLocationName
        # 4075900|2013-02-01T22:18:33|-11.12|165.378|10.0|NEIC|NEIC PDE|NEIC PDE-Q||MW|6.4|GCMT|SANTA CRUZ ISLANDS

        if (!isGeneric("getEvent")) {
          setGeneric("getEvent", function(obj, starttime, endtime, minmag, maxmag, magtype,
                                          mindepth, maxdepth) {
            standardGeneric("getEvent")
          })
        }

        # END of R documentation


        Returns a dataframe of events returned by the `event_url` source
        specified in the `user_request` object used to initialize the
        `Concierge`.

        By default, information in the `user_request` is used to generate
        a FDSN webservices request for event data. Where arguments are
        provided, these are used to override the information found in
        `user_request.

        :type starttime: :class:`~obspy.core.utcdatetime.UTCDateTime`
        :param starttime: Limit to metadata epochs starting on or after the
            specified start time.
        :type endtime: :class:`~obspy.core.utcdatetime.UTCDateTime`
        :param endtime: Limit to metadata epochs ending on or before the
            specified end time.
        :type minmagnitude: float, optional
        :param minmagnitude: Limit to events with a magnitude larger than the
            specified minimum.
        :type maxmagnitude: float, optional
        :param maxmagnitude: Limit to events with a magnitude smaller than the
            specified maximum.
        :type magnitudetype: str, optional
        :param magnitudetype: Specify a magnitude type to use for testing the
            minimum and maximum limits.
        :type mindepth: float, optional
        :param mindepth: Limit to events with depth, in kilometers, larger than
            the specified minimum.
        :type maxdepth: float, optional
        :param maxdepth: Limit to events with depth, in kilometers, smaller
            than the specified maximum.

        #.. rubric:: Example

        #>>> my_request =  UserRequest(dummy=True)
        #>>> concierge = Concierge(my_request)
        #>>> concierge.get_event() #doctest: +ELLIPSIS
        '
         eventId                         time  latitude  longitude  depth author...'
        """

        # Allow arguments to override UserRequest parameters
        if starttime is None:
            _starttime = self.requested_starttime
        else:
            _starttime = starttime
        if endtime is None:
            _endtime = self.requested_endtime
        else:
            _endtime = endtime

        if self.event_client is None:
            # Read local QuakeML file
            try:
                event_catalog = obspy.read_events(self.event_url)
            except Exception as e:
                err_msg = "The QuakeML file: '%s' is not valid" % self.event_url
                self.logger.debug(e)
                self.logger.error(err_msg)
                raise ValueError
            
            # events.columns
            # Index([u'eventId', u'time', u'latitude', u'longitude', u'depth', u'author',
            #        u'cCatalog', u'contributor', u'contributorId', u'magType', u'magnitude',
            #        u'magAuthor', u'eventLocationName'],
            #        dtype='object')
            #
            dataframes = []
            
            for event in event_catalog:
                origin = event.preferred_origin()
                magnitude = event.preferred_magnitude()
                df = pd.DataFrame({'eventId': re.sub('.*eventid=','',event.resource_id.id),
                                   'time': origin.time,
                                   'latitude': origin.latitude,
                                   'longitude': origin.longitude,
                                   'depth': origin.depth/1000, # QuakeML convention is meters, convert to kilometers
                                   'magType': magnitude.magnitude_type,
                                   'magnitude': magnitude.mag,
                                   'eventLocationName': event.event_descriptions[0].text},
                                  index=[0])
                dataframes.append(df)
                
            # Concatenate into the events dataframe
            events = pd.concat(dataframes, ignore_index=True)    
            if _starttime:
                events = events[events['time'] >= _starttime]
            if _endtime:
                events = events[events['time'] <= _endtime]
            if minmag:
                events = events[events['magnitude'] >= minmag]
            if maxmag:
                events = events[events['magnitude'] <= maxmag]
            if magtype:
                events = events[events['magType'].str.match(magtype, as_indexer=True)]
            if mindepth:
                events = events[events['depth'] >= mindepth]
            if maxdepth:
                events = events[events['depth'] <= maxdepth] 

            events.index=np.arange(1,len(events)+1)

        else:
            # Read from FDSN web services
            try:
                events = irisseismic.getEvent(self.event_url,
                                              starttime=_starttime,
                                              endtime=_endtime,
                                              minmag=minmag,
                                              maxmag=maxmag,
                                              magtype=magtype,
                                              mindepth=mindepth,
                                              maxdepth=maxdepth)

            except Exception as e:
                err_msg = "The event_url: '%s' returns an error" % (self.event_url)
                self.logger.debug(str(e).strip('\n'))
                self.logger.error(err_msg)
                raise

        if events.shape[0] == 0:
            return None # TODO:  raise an exception
        else:
            return events



if __name__ == '__main__':
    import doctest
    doctest.testmod(exclude_empty=True)
