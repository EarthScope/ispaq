"""
ISPAQ Preferences Loader and Container.

:copyright:
    Mazama Science
:license:
    GNU Lesser General Public License, Version 3
    (http://www.gnu.org/copyleft/lesser.html)
"""
import json
import ispaq.utils.preferences as preferences

from obspy import UTCDateTime


# Dummy UserRequest object
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
        self.metric_names = ["num_gaps"]  # TODO:  to be removed
        self.sncl_patterns = ["US.OXF..*"]
        self.metric_dictionary = {'simple': {'basicStats': ['sample_min','sample_max'],
                                             'gaps': ['num_gaps']} }
        # More to be added as needed


# Real UserRequest object
class UserRequest(object):
    def __init__(self, requested_start_time, requested_end_time, requested_metric_set, requested_sncl_alias, pref_file,
                 json_user_request=None):
        """
        Creates a UserRequest object.

        .. rubric:: Example

        TODO:  Generate doctest examples by loading from json.
        """

        #     Set fields from JSON if requested--------------------------------

        if json_user_request is not None:
            # Load json dictionary from file (or string)
            # TODO:  Test whether the `json` argument is a file or a string and
            # TODO:  use json.load() or json.loads() accordingly

            # Create new 'args' object
            # TODO:
            print("'json'_file argument not supported yet.")

        #     Set fields from arguments       ---------------------------------

        # desired metric set
        self.metric_set_name = requested_metric_set
        self.sncl_alias = requested_sncl_alias

        # start and end times
        self.requested_start_time = UTCDateTime(requested_start_time)

        if requested_end_time is None:
            self.requested_end_time = self.requested_start_time + (24 * 60 * 60)
        else:
            self.requested_end_time = UTCDateTime(requested_end_time)

        #     Load preferences from file      ---------------------------------

        # custom metrics sets and sncls
        self.custom_metric_sets, self.sncl_aliases = preferences.load(pref_file)

        # {irismustang function: custom metric set that they provide data for}, [sets that don't exist]
        self.required_metric_set_functions, dne_sets = preferences.validate_metric_sets(self.custom_metric_sets)

    def json_dump(self):
        """
        Dump a dictionary of UserRequest properties as a json string
        
        # TODO:  If a file argument is given, dump to a file with json.dump.
        # TODO:  Otherwise, return the json string.
        """

        properties_dict = {}
        
        # TODO:  Fill in properties_dict with all properties, converting from
        # TODO:  UTCDateTime with str(self.starttime) and str(self.endtime).
        
        properties_json = json.dumps(properties_dict)
        
        return properties_json
        

if __name__ == '__main__':
    import doctest
    doctest.testmod(exclude_empty=True)

