import ispaq.utils.preferences as preferences
from ispaq.utils.sncls import get_simple_sncls
import obspy


class UserRequests:
    """

    """
    def __init__(self, pref_file, metric_set_name, sncl_alias, start_time, end_time):

        # desired metric set
        self.metric_set_name = metric_set_name
        self.sncl_alias = sncl_alias

        # start and end times
        self.start_time, self.end_time = obspy.UTCDateTime(start_time), obspy.UTCDateTime(end_time)

        # custom metrics sets and sncls
        self.custom_metric_sets, self.sncl_aliases = preferences.load(pref_file)

        # {irismustang function: custom metric set that they provide data for}, [sets that don't exist]
        self.required_metric_set_functions, dne_sets = preferences.validate_metric_sets(self.custom_metric_sets)

    def single_day(self):
        """
        :returns: a tuple with the given start time + 1 day later
        """
        return self.start_time, self.start_time + (24 * 3600)
