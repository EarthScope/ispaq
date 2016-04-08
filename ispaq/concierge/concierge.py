"""
ISPAQ Data Access Expediter.

:copyright:
    Mazama Science
:license:
    GNU Lesser General Public License, Version 3
    (http://www.gnu.org/copyleft/lesser.html)
"""
# Use UTCDateTime internally for all times
from obspy import UTCDateTime
from obspy.clients.fdsn import Client
from obspy.clients.fdsn.header import URL_MAPPINGS

from ispaq.concierge.user_request import UserRequest

import pandas as pd


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
    def __init__(self, user_request):
        """
        Initializes the ISPAQ data access expediter.

        See :mod:`ispaq.concierge` for all parameters.
        """
        # Keep the entire UserRequest
        self.user_request = user_request
        
        # Copy important UserRequest properties to the Concierge for smpler access
        self.requested_starttime = user_request.requested_starttime
        self.requested_endtime = user_request.requested_endtime
        self.metric_names = user_request.metrics
        self.sncl_patterns = user_request.sncls
        self.function_by_logic = user_request.function_by_logic

        # TODO:  Should test for name (i.e. "IRIS"), full url or local file
        
        # Add event clients and URLs
        if user_request.event_url in URL_MAPPINGS.keys():
            self.event_client = Client(user_request.event_url)
            self.event_url = URL_MAPPINGS[user_request.event_url]
        else:
            print("TODO:  deal with non-URL_MAPPING event_url")

        # Add station clients and URLs 
        if user_request.station_url in URL_MAPPINGS.keys():
            self.station_client = Client(user_request.station_url)
            self.station_url = URL_MAPPINGS[user_request.station_url]
        else:
            print("TODO:  deal with non-URL_MAPPING station_url")

        # Add dataselect clients and URLs 
        if user_request.dataselect_url in URL_MAPPINGS.keys():
            self.dataselect_client = Client(user_request.dataselect_url)
            self.dataselect_url = URL_MAPPINGS[user_request.dataselect_url]
        else:
            print("TODO:  deal with non-URL_MAPPING dataselect_url")



    def get_events(self, starttime=None, endtime=None, minlatitude=None,
                   maxlatitude=None, minlongitude=None, maxlongitude=None,
                   latitude=None, longitude=None, minradius=None,
                   maxradius=None, mindepth=None, maxdepth=None,
                   minmagnitude=None, maxmagnitude=None, magnitudetype=None,
                   includeallorigins=None, includeallmagnitudes=None,
                   includearrivals=None, return_type="catalog"):
        """
        Query the event service of the client.

        :type starttime: :class:`~obspy.core.utcdatetime.UTCDateTime`, optional
        :param starttime: Limit to events on or after the specified start time.
        :type endtime: :class:`~obspy.core.utcdatetime.UTCDateTime`, optional
        :param endtime: Limit to events on or before the specified end time.
        :type minlatitude: float, optional
        :param minlatitude: Limit to events with a latitude larger than the
            specified minimum.
        :type maxlatitude: float, optional
        :param maxlatitude: Limit to events with a latitude smaller than the
            specified maximum.
        :type minlongitude: float, optional
        :param minlongitude: Limit to events with a longitude larger than the
            specified minimum.
        :type maxlongitude: float, optional
        :param maxlongitude: Limit to events with a longitude smaller than the
            specified maximum.
        :type latitude: float, optional
        :param latitude: Specify the latitude to be used for a radius search.
        :type longitude: float, optional
        :param longitude: Specify the longitude to the used for a radius
            search.
        :type minradius: float, optional
        :param minradius: Limit to events within the specified minimum number
            of degrees from the geographic point defined by the latitude and
            longitude parameters.
        :type maxradius: float, optional
        :param maxradius: Limit to events within the specified maximum number
            of degrees from the geographic point defined by the latitude and
            longitude parameters.
        :type mindepth: float, optional
        :param mindepth: Limit to events with depth, in kilometers, larger than
            the specified minimum.
        :type maxdepth: float, optional
        :param maxdepth: Limit to events with depth, in kilometers, smaller
            than the specified maximum.
        :type minmagnitude: float, optional
        :param minmagnitude: Limit to events with a magnitude larger than the
            specified minimum.
        :type maxmagnitude: float, optional
        :param maxmagnitude: Limit to events with a magnitude smaller than the
            specified maximum.
        :type magnitudetype: str, optional
        :param magnitudetype: Specify a magnitude type to use for testing the
            minimum and maximum limits.
        :type includeallorigins: bool, optional
        :param includeallorigins: Specify if all origins for the event should
            be included, default is data center dependent but is suggested to
            be the preferred origin only.
        :type includeallmagnitudes: bool, optional
        :param includeallmagnitudes: Specify if all magnitudes for the event
            should be included, default is data center dependent but is
            suggested to be the preferred magnitude only.
        :type includearrivals: bool, optional
        :param includearrivals: Specify if phase arrivals should be included.
        :type format: str
        :param format: return type ("catalog", "dataframe")

        TODO:  doctest example

        """

        # Get the information for the get_events() request if it is not provided
        if starttime is None:
            starttime = self.requested_starttime
        if endtime is None:
            endtime = self.requested_endtime

        if return_type.lower() == "catalog":
            print('TODO:  support "catalog" return type.')


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
        #>>> concierge.get_sncls() #doctest: +ELLIPSIS
        #[u'US.OXF..BHE', u'US.OXF..BHN', u'US.OXF..BHZ']
        """

        # Container for all of the individual SNCL dataframes generated
        dataframes = []
        
        for sncl_pattern in self.sncl_patterns:
            
            (UR_network, UR_station, UR_location, UR_channel) = sncl_pattern.split('.')
    
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
    
            # Get an Inventory object
            try:
                sncl_inventory = self.station_client.get_stations(starttime=_starttime, endtime=_endtime,
                                                                  network=_network, station=_station,
                                                                  location=_location, channel=_channel,
                                                                  level="channel")
            except Exception as e:
                print('\n*** ERROR in Concierge.get_sncls():  No sncls matching %s found at %s ***\n' % (sncl_pattern, self.station_url))
                continue
    
            # Walk through the Inventory object
            for n in sncl_inventory.networks:
                for s in n.stations:
                    for c in s.channels:
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
                        dataframes.append(df)
                            
        # END of sncl_patterns
        
        result = pd.concat(dataframes, ignore_index=True)    
           
        if result.shape[0] == 0:              
            return None # TODO:  raise an exception
        else:
            return result
    

if __name__ == '__main__':
    import doctest
    doctest.testmod(exclude_empty=True)
