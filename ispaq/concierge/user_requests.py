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

class UserRequest(object):
    def __init__(self, requested_start_time, requested_end_time, requested_metric_set, requested_sncl_alias, pref_file,
                 json_user_request=None, dummy_object=False):
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

        #     Create dummy object if requested---------------------------------
        elif dummy_object:
            self.requested_metric_set = 'dummySetName'
            self.requested_sncl_alias = 'dummySNCLAlias'
            self.requested_start_time = UTCDateTime("2002-04-20")
            self.requested_end_time = UTCDateTime("2002-04-21")
            self.custom_metric_sets = {'dummySetName': ['sample_min', 'sample_rms']}
            self.sncl_aliases = {'dummySNCLAlias': ['US.OXF..BHZ', 'IU.OXF..BH?']}
            self.required_metric_set_functions = {'basicStats': 'dummySetName'}
            self.dne_metrics = None
            self.event_url = "IRIS"
            self.station_url = "IRIS"
            self.dataselect_url = "IRIS"

        #     Set fields from arguments       ---------------------------------
        else:
            # desired metric set
            self.requested_metric_set = requested_metric_set
            self.requested_sncl_alias = requested_sncl_alias

            # start and end times
            self.requested_start_time = UTCDateTime(requested_start_time)

            if requested_end_time:
                self.requested_end_time = UTCDateTime(requested_end_time)
            else:
                self.requested_end_time = self.requested_start_time + (24 * 60 * 60)

            #     Load preferences from file      ---------------------------------

            # custom metrics sets and sncls
            custom_metric_sets, custom_sncl = {}, {}
            current = None
            for line in pref_file:  # parse file
                line = line.split('#')[0].strip() # remove comments
                if line.lower() == "custom metric sets:":  # metric header
                    current = 'm'
                elif line.lower() == "sncl aliases:":  # sncl header
                    current = 's'
                elif current is not None:  # line following header
                    entry = line.split(':')
                    if len(entry) <= 1:  # empty line
                        name, values = None, None
                    else:  # non-empty line
                        name = entry[0]
                        values = entry[1].strip().split(',')
                        values = [value.strip() for value in values]
                        values = filter(None, values)  # remove empty strings
                    if name is None:
                        pass
                    elif current == 'm':
                        custom_metric_sets[name] = values
                    elif current == 's':
                        custom_sncl[name] = values

            self.custom_metric_sets, self.sncl_aliases = custom_metric_sets, custom_sncl

            # {irismustang function: custom metric set that they provide data for}, [metrics that don't exist]
            self.required_metric_set_functions, self.dne_metrics = preferences.validate_metric_sets(self.custom_metric_sets)

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

    def __str__(self):
        return "UserRequest Object @ %s: \n\t" \
               "requested metric set: %s \n\t" \
               "requested sncl alias: %s \n\t" \
               "requested start time: %s \n\t" \
               "requested end time: %s \n\t" \
               "custom metric sets: %s \n\t" \
               "requested metrics that dne: %s \n\t" \
               "custom sncl aliases: %s \n\t" \
               "required metric set functions: %s \n" % (hex(id(self)),
                                                         self.requested_metric_set,
                                                         self.requested_sncl_alias,
                                                         self.requested_start_time,
                                                         self.requested_end_time,
                                                         self.custom_metric_sets,
                                                         self.dne_metrics,
                                                         self.sncl_aliases,
                                                         self.required_metric_set_functions)
        

if __name__ == '__main__':
    import doctest
    doctest.testmod(exclude_empty=True)

