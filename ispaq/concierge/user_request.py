"""
ISPAQ Preferences Loader and Container.

:copyright:
    Mazama Science
:license:
    GNU Lesser General Public License, Version 3
    (http://www.gnu.org/copyleft/lesser.html)
"""
from os.path import expanduser
import json

# Use UTCDateTime internally for all times
from obspy import UTCDateTime

# The metricslist function returns a dictionary information on "metric sets",
# "business logic" and "metric names".
# TODO:  metricslist should be a function in the R irisMustangMetrics package.
from ispaq.irismustangmetrics.metrics import metricslist


class UserRequest(object):
    """
    The user_request class is in charge of parsing arguments issued on the
    command line, loading and parsing a preferences file and setting a bunch
    of properties that capture the totality of what the user wants in a single
    invocation of the ISPAQ top level script.

    Properties that must be specified include at a minimum:
     * metric_names[]
     * sncl_patterns[]
     * starttime
     * endtime
     * event_url
     * station_url
     * dataselect_url

    All methods are internal except for load_json() and dump_json() which can
    be used for debugging. The user_request will be stored by the concierge
    for future reference.

    Think of the methods of the user_request object as the work of a lower
    level front desk person who is taking guest information from a handwritten
    request (preferences file) and phone call (command line arguments)
    and transcribing that info[ onto a standard form that the cocierge keeps
    for each guest. (Each unique invocation of this script is a new 'guest'.)

    When the guest asks for something later, the concierge has already done
    the background work and can provide the guest whatever they want in their
    preferred format.
    """
    def __init__(self,
                 requested_starttime=None, requested_endtime=None,
                 requested_metric_set=None, requested_sncl_set=None,
                 pref_file=None, json_representation=None, dummy=False):
        """
        Creates a UserRequest object.

        .. rubric:: Example

        TODO:  Generate doctest examples by loading from json.
        """

        #     Initialize from JSON     ----------------------------------------

        if json_representation is not None:
            # Load json dictionary from file (or string)
            try:
                with open(expanduser(json_representation), 'r') as infile:
                    representation = json.load(infile)
            except IOError:
                representation = json.loads(json_representation)

            self.requested_starttime = UTCDateTime(representation['requested_starttime']["timestamp"])
            self.requested_endtime = UTCDateTime(representation['requested_endtime']["timestamp"])
            self.requested_metric_set = representation['requested_metric_set']
            self.requested_sncl_set = representation['requested_sncl_set']

            self.custom_metric_sets = representation['custom_metric_sets']
            self.sncl_sets = representation['sncl_sets']
            self.required_metric_set_functions = representation['required_metric_set_functions']
            self.dne_metrics = representation['dne_metrics']
            self.event_url = representation['event_url']
            self.station_url = representation['station_url']
            self.dataselect_url = representation['dataselect_url']


        #     Initialize a dummy object     -----------------------------------

        elif dummy:
            self.requested_starttime = UTCDateTime("2002-04-20")
            self.requested_endtime = UTCDateTime("2002-04-21")
            self.requested_metric_set = 'dummy_metric_set'
            self.requested_sncl_set = 'dummy_sncl_set'

            self.custom_metric_sets = {'dummySetName': ['sample_min', 'sample_rms']}
            self.sncl_sets = {'dummySNCLAlias': ['US.OXF..BHZ', 'IU.OXF..BH?']}
            self.required_metric_set_functions = {'basicStats': 'dummySetName'}
            self.dne_metrics = None
            self.event_url = "IRIS"
            self.station_url = "IRIS"
            self.dataselect_url = "IRIS"


        #     Initialize from arguments       ---------------------------------

        else:
            # start and end times
            self.requested_starttime = UTCDateTime(requested_starttime)
            if requested_endtime is None:
                self.requested_endtime = self.requested_starttime + (24 * 60 * 60)
            else:
                self.requested_endtime = UTCDateTime(requested_endtime)

            # metric and sncl sets
            self.requested_metric_set = requested_metric_set
            self.requested_sncl_set = requested_sncl_set

            #     Load preferences from file      -----------------------------

            # custom metrics sets and sncls
            custom_metric_sets, custom_sncl, custom_urls = {}, {}, {}
            currentSection = None
            for line in pref_file:  # parse file
                line = line.split('#')[0].strip()  # remove comments
                if line.lower() == "metrics:":  # metric header
                    currentSection = 'metric'
                elif line.lower() == "sncls:":  # sncl header
                    currentSection = 'sncl'
                elif line.lower() == "data services:":
                    currentSection = 'data_services'
                elif currentSection is not None:  # line following header
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
                    elif currentSection == 'metric':
                        custom_metric_sets[name] = values
                    elif currentSection == 'sncl':
                        custom_sncl[name] = values
                    elif currentSection == 'data_services':
                        custom_urls[name] = values[0]

            self.custom_metric_sets, self.sncl_sets = custom_metric_sets, custom_sncl
            ###print(custom_urls)
            self.dataselect_url = custom_urls['dataselect_url']
            self.event_url = custom_urls['event_url']
            self.station_url = custom_urls['station_url']

            #     Finding required metric_set functions----------------------------

            print('Validating custom metrics...')
            error_list = []
            custom_metricset_functions = {}
            metric_functions = metricslist() # this is a dictionary: function_name > contained_metrics

            # Creates a dictionary of {needed functions: [list of needed metrics that they provide]}
            for custom_metricset in custom_metric_sets:
                required_functions = {}
                for metric in custom_metric_sets[custom_metricset]:
                    try:  # check if metric exists
                        function = metric_functions[metric]
                    except KeyError:
                        print('\033[93m   Metric "%s" not found\033[0m' % metric)
                        error_list.append(metric)

                    if function in required_functions:
                        required_functions[function].append(metric)
                    else:
                        required_functions[function] = [metric]

                custom_metricset_functions[custom_metricset] = required_functions

            print('Finished validating with \033[93m%d\033[0m errors.\n' % len(error_list))

            # {irismustang function: custom metric set that they provide data for}, [metrics that don't exist]
            self.required_metric_set_functions, self.dne_metrics = custom_metricset_functions, error_list


    def json_dump(self, file_loc=None):
        """
        Dump a dictionary of UserRequest properties as a json string
        Does not catch IOError if file_loc is invalid
        :param file_loc: location to write json
        :return: json string representation of internal properties

        >>> u = UserRequest(dummy=True)
        >>> output = u.json_dump()
        >>> output #doctest: +ELLIPSIS
        '{"custom_metric_sets": ... "event_url": "IRIS", ... "dataselect_url": "IRIS", "dne_metrics": null}'
        >>> s = UserRequest(json_representation=output)
        >>> s.json_dump() #doctest: +ELLIPSIS
        '{"custom_metric_sets": ... "event_url": "IRIS", ... "dataselect_url": "IRIS", "dne_metrics": null}'
        """

        json_string = json.dumps(self, default=lambda o: o.__dict__)
        if file_loc is not None:
            with open(expanduser(file_loc), 'w') as outfile:
                outfile.write(json_string)
        return json_string


    def __str__(self):
        return self.json_dump()
        

if __name__ == '__main__':
    import doctest
    doctest.testmod(exclude_empty=True)

