"""
ISPAQ Data Access Expediter.

:copyright:
    Mazama Science
:license:
    GNU Lesser General Public License, Version 3
    (http://www.gnu.org/copyleft/lesser.html)
"""

from __future__ import (absolute_import, division, print_function)

import os
import re
import glob

import pandas as pd

import obspy
from obspy.clients.fdsn import Client
from obspy.clients.fdsn.header import URL_MAPPINGS

# ISPAQ modules
from .user_request import UserRequest
from . import irisseismic


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
        
        # Copy important UserRequest properties to the Concierge for smpler access
        self.requested_starttime = user_request.requested_starttime
        self.requested_endtime = user_request.requested_endtime
        self.metric_names = user_request.metrics
        self.sncl_patterns = user_request.sncls
        self.function_by_logic = user_request.function_by_logic
        self.logic_types = user_request.function_by_logic.keys()
        
        # Individual elements from the Preferences: section of the preferences file
        self.csv_output_dir = user_request.csv_output_dir
        self.plot_output_dir = user_request.plot_output_dir
        self.sigfigs = user_request.sigfigs
        
        # Output information
        file_base = '%s_%s_%s' % (self.user_request.requested_metric_set,
                                  self.user_request.requested_sncl_set, 
                                  self.requested_starttime.date)
        self.output_file_base = self.csv_output_dir + '/' + file_base
        
        # Add dataselect clients and URLs or reference a local file
        if user_request.dataselect_url in URL_MAPPINGS.keys():
            # Get data from FDSN dataselect service
            self.dataselect_url = URL_MAPPINGS[user_request.dataselect_url]
            self.dataselect_client = Client(user_request.dataselect_url)
        else:
            if os.path.exists(os.path.abspath(user_request.dataselect_url)):
                # Get data from local miniseed files
                self.dataselect_url = os.path.abspath(user_request.dataselect_url)
                self.dataselect_client = None
            else:
                err_msg = "Cannot find preference file dataselect_url: '%s'" % user_request.dataselect_url
                self.logger.error(err_msg)
                raise ValueError(err_msg)

        # Add event clients and URLs or reference a local file
        if user_request.event_url in URL_MAPPINGS.keys():
            self.event_url = URL_MAPPINGS[user_request.event_url]
            self.event_client = Client(user_request.event_url)
        else:
            if os.path.exists(os.path.abspath(user_request.event_url)):
                # Get data from local QUAKEML files
                self.event_url = os.path.abspath(user_request.event_url)
                self.event_client = None
            else:
                err_msg = "Cannot find preference file event_url: '%s'" % user_request.event_url
                self.logger.error(err_msg)
                raise ValueError(err_msg)

        # Add station clients and URLs or reference a local file
        if user_request.station_url in URL_MAPPINGS.keys():
            self.station_url = URL_MAPPINGS[user_request.station_url]
            self.station_client = Client(user_request.station_url)
        else:
            if os.path.exists(os.path.abspath(user_request.station_url)):
                # Get data from local StationXML files
                self.station_url = os.path.abspath(user_request.station_url)
                self.station_client = None
            else:
                err_msg = "Cannot find preference file station_url: '%s'" % user_request.station_url
                self.logger.error(err_msg)
                raise ValueError(err_msg)



    def get_availability(self,
                         network=None, station=None, location=None, channel=None,
                         starttime=None, endtime=None, includerestricted=None,
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
        #   http://service.iris.edu/fdsnws/station/1/
        #
        # #Network | Station | Location | Channel | Latitude | Longitude | Elevation | Depth | Azimuth | Dip | Instrument | Scale | ScaleFreq | ScaleUnits | SampleRate | StartTime | EndTime
        # CU|ANWB|00|LHZ|17.66853|-61.78557|39.0|0.0|0.0|-90.0|Streckeisen STS-2 Standard-gain|2.43609E9|0.05|M/S|1.0|2010-02-10T18:35:00|2599-12-31T23:59:59
        #
        ################################################################################
        
        if (!isGeneric("getAvailability")) {
          setGeneric("getAvailability", function(obj, network, station, location, channel,
                                                 starttime, endtime, includerestricted,
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
        `user_request.

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
        :type includerestricted: bool
        :param includerestricted: Specify if results should include information
            for restricted stations.
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

        # Container for all of the individual SNCL dataframes generated
        dataframes = []
        
        for sncl_pattern in self.sncl_patterns:
            
            (UR_network, UR_station, UR_location, UR_channel) = sncl_pattern.split('.')

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


            # NOTE:  As currently implemented in v0.7.10, a single local stationXML file is read in multiple
            # NOTE:  times when multiple patterns are supplied. This will result in duplicate rows when the 
            # NOTE:  dataframes are concatenated. The most expedient way to deal with this without significant
            # NOTE:  refactoring is to simple remove duplicate rows in the result dataframe before returning.
            
            if self.station_client is None:
                # Read a single, local StationXML file
                try:
                    sncl_inventory = obspy.read_inventory(self.station_url)
                except Exception as e:
                    err_msg = "The StationXML file: '%s' is not valid" % self.station_url
                    self.logger.debug(e)
                    self.logger.error(err_msg)   
                    raise ValueError(err_msg)
                
                # Filter inventory for this sncl_pattern
                debugPoint = 1
            
            else:
                # Read from FDSN web services
                #
                # TODO:  Should use "includeAvailability=true, matchtimeseries=true" if these are supported.
                # TODO:  But we need to handle cases and reissue without these arguments when they are not supported.
                # TODO:  Is all this even worth the bother if we skip SNCLs that don't return data?
                try:
                    sncl_inventory = self.station_client.get_stations(starttime=_starttime, endtime=_endtime,
                                                                      network=_network, station=_station,
                                                                      location=_location, channel=_channel,
                                                                      includerestricted=None,
                                                                      latitude=latitude, longitude=longitude,
                                                                      minradius=minradius, maxradius=maxradius,                                                                
                                                                      level="channel")
                except Exception as e:
                    err_msg = "No sncls matching %s found at %s" % (sncl_pattern, self.station_url)
                    self.logger.debug(e)
                    self.logger.warning(err_msg)
                    continue


            # NOTE:  We need to do regular expression matching of the SNCL pattern here to support local
            # NOTE:  StationXML files which may list many files that are not in the request.  FDSN web 
            # NOTE:  services only return matching SNCLs but this extra check is quick.
            
            # Modify FDSN wildcards so they match python regular expressions
            # NOTE:  We have to ensure that net, sta, loc, cha are <type 'str'> and not <type 'unicode'>
            network_re = str.replace(str(_network),'*','.*')
            station_re = str.replace(str(_station),'*','.*')
            location_re = str.replace(str(_location),'*','.*')
            channel_re = str.replace(str(_channel),'*','.*')
            
            # Walk through the Inventory object
            for n in sncl_inventory.networks:
                if (re.search(network_re, n.code) != None):
                    for s in n.stations:
                        if (re.search(station_re, s.code) != None):
                            for c in s.channels:
                                if ( (re.search(location_re, c.location_code) != None) and (re.search(channel_re, c.code) != None) ): 
                                    # "network"    "station"    "location"   "channel"    "latitude"   "longitude"  "elevation"  "depth"      "azimuth"    "dip"        "instrument"
                                    # "scale"      "scalefreq"  "scaleunits" "samplerate" "starttime"  "endtime"    "snclId"         
                                    df = pd.DataFrame({'network': n.code,
                                                       'station': s.code,
                                                       'location': c.location_code,
                                                       'channel': c.code,
                                                       'latitude': c.latitude,
                                                       'longitude': c.longitude,
                                                       'elevation': c.elevation,
                                                       'depth': c.depth,
                                                       'azimuth': c.azimuth,
                                                       'dip': c.dip,
                                                       'instrument': c.sensor.description,
                                                       'scale': None,          # TODO:  Figure out how to get instrument 'scale'
                                                       'scalefreq': None,      # TODO:  Figure out how to get instrument 'scalefreq'
                                                       'scaleunits': None,     # TODO:  Figure out how to get instrument 'scaleunits'
                                                       'samplerate': c.sample_rate,
                                                       'starttime': c.start_date,
                                                       'endtime': c.end_date,
                                                       'snclId': n.code + "." + s.code + "." + c.location_code + "." + c.code},
                                                      index=[0])
                                    
                                    # NOTE:  See notes above reading of local stationXML
                                    if ( len(dataframes) == 0 or self.station_client is not None):
                                        dataframes.append(df)
                            
        # END of sncl_patterns
        
        if len(dataframes) == 0:
            err_msg = "No available waveforms matching" + str(self.sncl_patterns)
            self.logger.info(err_msg)
            raise NoAvailableDataError(err_msg)
        
        else:
            result = pd.concat(dataframes, ignore_index=True)
                
            # TODO:  Maybe the concierge should remember this dataframe for cases like SNR which have get_availability() inside
            # TODO:  of a get_event() loop.
               
            if result.shape[0] == 0:              
                err_msg = "No available waveforms matching" + str(self.sncl_patterns)
                self.logger.info(err_msg)
                raise NoAvailableDataError(err_msg)
            else:
                return result
    

    def get_dataselect(self,
                       network=None, station=None, location=None, channel=None,
                       starttime=None, endtime=None, quality="B",
                       inclusiveEnd=True, ignoreEpoch=False):
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

        if self.dataselect_client is None:
            # Read local MINIseed file and convert to R_Stream
            filename = '%s.%s.%s.%s.%s' % (network, station, location, channel, _starttime.strftime('%Y.%j'))
            filepattern = self.dataselect_url + '/' + filename + '*' # Allow for possible quality codes
            matchingFiles = glob.glob(filepattern)
            
            if (len(matchingFiles) == 0):
                self.logger.info("No files found matching '%s'" % (filepattern))
                
            else:
                filepath = matchingFiles[0]
                if (len(matchingFiles) > 1):
                    self.logger.warning("Multiple files found matching" '%s -- using %s' % (filepattern, filepath))
                try:
                    # Get the ObsPy version of the stream
                    py_stream = obspy.read(filepath)
                    py_stream = py_stream.slice(_starttime, _endtime)
                    # NOTE:  ObsPy does not store state-of-health flags with each stream.
                    # NOTE:  We need to read them in separately from the miniseed file.
                    flag_dict = obspy.io.mseed.util.get_timing_and_data_quality(filepath)
                    act_flags = [0,0,0,0,0,0,0,0] # TODO:  Find a way to read act_flags
                    io_flags = [0,0,0,0,0,0,0,0] # TODO:  Find a way to read io_flags
                    dq_flags = flag_dict['data_quality_flags']
                    # NOTE:  ObsPy does not store station metadata with each trace.
                    # NOTE:  We need to read them in separately from station metadata.
                    availability = self.get_availability(network, station, location, channel, _starttime, _endtime)
                    sensor = availability.instrument[0]
                    scale = availability.scale[0]
                    scalefreq = availability.scalefreq[0]
                    scaleunits = availability.scaleunits[0]
                    if sensor is None: sensor = ""           # default from IRISSeismic Trace class prototype
                    if scale is None: scale = 1.0            # default from IRISSeismic Trace class prototype
                    if scalefreq is None: scalefreq = 1.0    # default from IRISSeismic Trace class prototype
                    if scaleunits is None: scaleunits = ""   # default from IRISSeismic Trace class prototype
                    latitude = availability.latitude[0]
                    longitude = availability.longitude[0]
                    elevation = availability.elevation[0]
                    depth = availability.depth[0]
                    azimuth = availability.azimuth[0]
                    dip = availability.dip[0]
                    # Create the IRISSeismic version of the stream
                    r_stream = irisseismic.R_Stream(py_stream, _starttime, _endtime, act_flags, io_flags, dq_flags,
                                                    sensor, scale, scalefreq, scaleunits, latitude, longitude, elevation, depth, azimuth, dip)
                except Exception as e:
                    err_msg = "Error reading in local waveform from %s" % filepath
                    self.logger.debug(e)
                    self.logger.error(err_msg)
                    raise
        else:
            # Read from FDSN web services
            try:
                r_stream = irisseismic.R_getDataselect(self.dataselect_url, network, station, location, channel, _starttime, _endtime, quality, inclusiveEnd, ignoreEpoch)
            except Exception as e:
                err_msg = "Error reading in waveform from %s webservice" % self.dataselect_client
                self.logger.debug(e)
                self.logger.error(err_msg)
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
        #   http://service.iris.edu/fdsnws/event/1/
        #
        # TODO:  The getEvent method could be fleshed out with a more complete list
        # TODO:  of arguments to be used as ws-event parameters.
        ################################################################################
        
        # http://service.iris.edu/fdsnws/event/1/query?starttime=2013-02-01T00:00:00&endtime=2013-02-02T00:00:00&minmag=5&format=text
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
                err_msg = "The StationXML file: '%s' is not valid." % self.station_url
                self.logger.debug(e)
                self.logger.error(err_msg)
                raise ValueError(err_msg)
            
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
                                   'depth': origin.depth/1000, # IRIS event webservice returns depth in km # TODO:  check this
                                   'author': origin.creation_info.author,
                                   'cCatalog': None,
                                   'contributor': None,
                                   'contributorId': None,
                                   'magType': magnitude.magnitude_type,
                                   'magnitude': magnitude.mag,
                                   'magAuthor': magnitude.creation_info.author,
                                   'eventLocationName': event.event_descriptions[0].text},
                                  index=[0])
                dataframes.append(df)
                
            # Concatenate into the events dataframe
            events = pd.concat(dataframes, ignore_index=True)    

        else:
            # Read from FDSN web services
            # TODO:  Need to make sure irisseismic.getEvent uses any FDSN site
            try:
                events = irisseismic.getEvent(starttime=_starttime,
                                              endtime=_endtime,
                                              minmag=minmag,
                                              maxmag=maxmag,
                                              magtype=magtype,
                                              mindepth=mindepth,
                                              maxdepth=maxdepth)

            except Exception as e:
                err_msg = "The event_url: '%s' returns an error" % (self.event_url)
                self.logger.debug(e)
                self.logger.error(err_msg)
                raise


        if events.shape[0] == 0:
            return None # TODO:  raise an exception
        else:
            return events



if __name__ == '__main__':
    import doctest
    doctest.testmod(exclude_empty=True)
