from ispaq.irisseismic.webservices import *
import obspy
from rpy2.rinterface import RRuntimeError
from ispaq.irismustangmetrics.metrics import applySimpleMetric
import pandas as pd


def get_snr_for_available_sncl(availability_row, event_time, event_latitude,
                               event_longitude, event_depth, window_secs=60):
    """
    :param availability_row: a row from a getAvailability dataframe
    :param event_time: the time of the event
    :param event_latitude: the latitude of the event
    :param event_longitude: the longitude of the event
    :param event_depth: the depth of the event
    :param window_secs:
    :returns a series object of the SNR metric row
    """
    none_series = pd.Series([None] * 6)
    try:
        travel_time_df = getTraveltime(event_latitude, event_longitude, event_depth, availability_row.latitude,
                                       availability_row.longitude)

        if (travel_time_df.phaseName == 'P').any():  # TODO This check might not be needed
            travel_time = travel_time_df.travelTime[travel_time_df.phaseName == 'P'][1]
        else:
            travel_time = travel_time_df['travelTime'][1]  # r is 1 based

        # SNR window with +/- 1 to deal with rounding at service
        window_start = event_time + travel_time - window_secs/2 - 1
        window_end = event_time + travel_time + window_secs/2 + 1

        stream = get_dataselect(availability_row.network, availability_row.station, availability_row.location,
                                availability_row.channel, window_start, window_end)

        # check for gaps in middle
        if len(stream.slots['traces']) > 1:
            print('gaps in stream')
            return none_series

        # check for for gaps at either end
        trace = stream.slots['traces'][0]
        trace_stats = trace.slots['stats']
        if trace_stats.slots['starttime'] > window_start or trace_stats.slots['endtime'] < window_end:
            print('gaps at end(s) of stream')
            return none_series

        metric_output = applySimpleMetric(stream, 'SNR', windowSecs=window_secs)
        return metric_output.iloc[0]  # convert to series

    except RRuntimeError as e:
        print(e)

    return none_series


def get_snr_for_event(event, sncl, max_radius=180):
    """
    produces snr metric values for a given event
    :param event: getEvent dataframe row
    :param sncl: a sncl string
    :param max_radius: the max radius to check for events
    :returns a dataframe of metric values
    """
    none_series = pd.Series([None] * 6)  # value to return if anything fails

    if event.latitude is None or event.longitude is None:
        print('Skipping %s since no location data' % event.eventId)
        return none_series

    if event.depth is None:
        print('Skipping %s since no depth data' % event.eventId)
        return none_series

    event_time = obspy.UTCDateTime(event.time)
    start_time = event_time - (60 * 2)  # 2 min prior to event
    end_time = event_time + (60 * 28)  # 28 min after

    try:
        availability = getAvailability(sncl, start_time, end_time, event.latitude, event.longitude,
                                       minradius=0, maxradius=max_radius)

        if availability is None or len(availability) == 0:
            print('Skipping %s since no sncl was available' % event.eventId)
            return none_series

        df = availability.apply(lambda row: get_snr_for_available_sncl(row, event_time, event.latitude,
                                                                       event.longitude, event.depth), axis=1)

        return df  # wrapped so that apply can handle it

    except RRuntimeError as e:
        print(e)
        print("Skipping %s %s event at %s because there are no nearby SNCLs" % (event.time, event.magnitude,
                                                                                event.eventLocationName))
    return none_series


def main(sncl, start, end, max_radius):
    print("Working...")
    events = getEvent(starttime=obspy.UTCDateTime(start),
                      endtime=obspy.UTCDateTime(end))
    events = events[0:5]
    series_of_listdfs = events.apply(lambda event: [get_snr_for_event(event, sncl, max_radius)], axis=1)

    list_of_listdfs = series_of_listdfs.tolist()  # converts series to list
    list_of_dfs = [item for sublist in list_of_listdfs for item in sublist]  # flattens list of lists
    print(list_of_dfs)
    unfiltered_df = pd.concat(list_of_dfs)  # joins list of dataframes

    final_df = unfiltered_df.dropna()  # filter out handled errors

    print(final_df)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--sncl', action='store', default=False,
                        help='Network.Station.Location.Channel identifier (e.g. US.OXF..BHZ)')
    parser.add_argument('--start', action='store', default=False,
                        help='start time in ISO 8601 format')
    parser.add_argument('--end', action='store', default=False,
                        help='end time in ISO 8601 format')
    parser.add_argument('--max-radius', action='store', default=180,
                        help='max radius')
    args = parser.parse_args()

    main(args.sncl, args.start, args.end, args.max_radius)
