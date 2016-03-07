# Testing ObsPy with FDSN web services
#
# see http://docs.obspy.org/packages/obspy.fdsn.html

# List all FDSN locations (example from link above) ----------------------------

from obspy import UTCDateTime

from obspy.fdsn import Client
client = Client("IRIS")

from obspy.fdsn.header import URL_MAPPINGS
for key in sorted(URL_MAPPINGS.keys()):
    print("{0:<7} {1}".format(key,  URL_MAPPINGS[key]))
    

# Inventory (from link above) --------------------------------------------------

starttime = UTCDateTime("2002-01-01")
endtime = UTCDateTime("2002-01-02")

inventory = client.get_stations(network="IU", station="A*",
                                starttime=starttime,
                                endtime=endtime)

print(inventory)


# NCEDC channels request -------------------------------------------------------

client = Client("NCEDC")

starttime = UTCDateTime("2015-07-07")
endtime = UTCDateTime("2015-07-08")


# NOTE:  Good documentation on STATIONXML and the ObsPy "Inventory" object is here:
# NOTE:
# NOTE:  http://docs.obspy.org/packages/obspy.station.html


# Just the networks --------------------

network_inventory = client.get_stations(starttime=starttime,endtime=endtime,level="network")

# What's inside this?
len(network_inventory.networks) # 23
network_inventory.networks[0].get_contents()


# Stations at a network ----------------

station_inventory = client.get_stations(network="CI",starttime=starttime,endtime=endtime,level="station")

# What's inside this?
len(station_inventory.networks) # 1
station_inventory.networks[0].get_contents()['stations']


# Channels at a station ----------------

channels_inventory = client.get_stations(network="CI",station="B*",channel="BH?",starttime=starttime,endtime=endtime,level="channel")

# What's inside this?
len(channels_inventory.networks) # 1
station_inventory.networks[0].get_contents()['channels']


# NOTE:  The only keys in a Network object are 
