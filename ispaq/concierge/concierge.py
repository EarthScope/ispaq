"""
ISPAQ Data Access Expediter.

:copyright:
    Mazama Science
:license:
    GNU Lesser General Public License, Version 3
    (http://www.gnu.org/copyleft/lesser.html)
"""
from obspy import UTCDateTime
from obspy.clients.fdsn import Client

import pandas as pd


# Dummy user_request object
class DummyUserRequest(object):
    def __init__(self):
        """
        Creates a dummy UserRequest object with sufficient properties for testing.
        .. rubric:: Example

        >>> my_request =  DummyUserRequest()
        >>> my_request.sncl_patterns
        ['US.OXF..*']
        """
        self.starttime = UTCDateTime("2002-04-20")
        self.endtime = UTCDateTime("2002-04-21")
        self.event_url = "IRIS"
        self.station_url = "IRIS"
        self.dataselect_url = "IRIS"
        self.metric_names = ["num_gaps"]
        self.sncl_patterns = ["US.OXF..*"]


class Concierge(object):
    """
    ISPAQ Data Access Expediter.

    :type user_request: :class:`~ispaq.concierge`
    :param user_request: User request containing the combination of command-line
        arguments and information from the parsed user preference file.

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
        self.user_request = user_request

        # Create a new webservice clients
        self.event_client = Client(self.user_request.event_url)
        self.station_client = Client(self.user_request.station_url)
        self.dataselect_client = Client(self.user_request.dataselect_url)

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
            starttime = self.user_request.starttime
        if endtime is None:
            endtime = self.user_request.endtime

        if return_type.lower() == "catalog":
            print('TODO:  support "catalog" return type.')



    def get_sncls(self, starttime=None, endtime=None,
                  network=None, station=None, location=None, channel=None,
                  minlatitude=None, maxlatitude=None, minlongitude=None,
                  maxlongitude=None, latitude=None, longitude=None,
                  minradius=None, maxradius=None, level=None,
                  includerestricted=None, includeavailability=None,
                  updatedafter=None, matchtimeseries=None,
                  return_type="list"):
        """
        Returns a list of SNCLs available from the `station_url` source
        specified in the `user_request` object used to initialize the
        `Concierge`.

        By default, information in the `user_request` is used to generate
        a FDSN webservices request for station data. Where arguments are
        provided, these are used to override the information found in
        `user_request.

        :type starttime: :class:`~obspy.core.utcdatetime.UTCDateTime`
        :param starttime: Limit to metadata epochs starting on or after the
            specified start time.
        :type endtime: :class:`~obspy.core.utcdatetime.UTCDateTime`
        :param endtime: Limit to metadata epochs ending on or before the
            specified end time.
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
        :type minlatitude: float
        :param minlatitude: Limit to stations with a latitude larger than the
            specified minimum.
        :type maxlatitude: float
        :param maxlatitude: Limit to stations with a latitude smaller than the
            specified maximum.
        :type minlongitude: float
        :param minlongitude: Limit to stations with a longitude larger than the
            specified minimum.
        :type maxlongitude: float
        :param maxlongitude: Limit to stations with a longitude smaller than
            the specified maximum.
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
        :type level: str
        :param level: Specify the level of detail for the results ("network",
            "station", "channel", "response"), e.g. specify "response" to get
            full information including instrument response for each channel.
        :type includerestricted: bool
        :param includerestricted: Specify if results should include information
            for restricted stations.
        :type includeavailability: bool
        :param includeavailability: Specify if results should include
            information about time series data availability.
        :type updatedafter: :class:`~obspy.core.utcdatetime.UTCDateTime`
        :param updatedafter: Limit to metadata updated after specified date;
            updates are data center specific.
        :type matchtimeseries: bool
        :param matchtimeseries: Only include data for which matching time
            series data is available.
        :type return_type: str
        :param return_type: return type ("dataframe", "inventory", "list")

        .. rubric:: Example

        >>> my_request =  DummyUserRequest()
        >>> gustave = Concierge(my_request)
        >>> gustave.get_sncls() #doctest: +ELLIPSIS
        [u'US.OXF..BHE', u'US.OXF..BHN', ... u'US.OXF..LHN', u'US.OXF..LHZ']
        """

        # Get the information for the get_stations() request if it is not provided
        (ur_network, ur_station, ur_location, ur_channel) = self.user_request.sncl_patterns[0].split('.')

        if starttime is None:
            starttime = self.user_request.starttime
        if endtime is None:
            endtime = self.user_request.endtime
        if network is None:
            network = ur_network
        if station is None:
            station = ur_station
        if location is None:
            location = ur_location
        if channel is None:
            channel = ur_channel

        # Get an Inventory object
        sncl_inventory = self.station_client.get_stations(starttime=starttime, endtime=endtime,
                                                          network=network, station=station,
                                                          location=location, channel=channel,
                                                          level="channel")

        if return_type.lower() == "inventory":
            return sncl_inventory

        elif return_type.lower() == "list":
            sncl_list = []
            # Walk through the Inventory object
            for n in sncl_inventory.networks:
                for s in n.stations:
                    for c in s.channels:
                        sncl = n.code + "." + s.code + "." + c.location_code + "." + c.code
                        sncl_list.append(sncl)
            return sncl_list

        else:
            return None # TODO:  return an exception



if __name__ == '__main__':
    import doctest
    doctest.testmod(exclude_empty=True)
