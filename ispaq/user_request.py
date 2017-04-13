"""
ISPAQ Preferences Loader and Container.

:copyright:
    Mazama Science
:license:
    GNU Lesser General Public License, Version 3
    (http://www.gnu.org/copyleft/lesser.html)
"""

from __future__ import (absolute_import, division, print_function)

import os
import json
import re

from obspy import UTCDateTime

# ISPAQ modules
from . import irismustangmetrics

from .ispaq import currentispaq

class UserRequest(object):
    """
    The UserRequest class is in charge of parsing arguments issued on the
    command line, loading and parsing a preferences file, and setting a bunch
    of properties that capture the totality of what the user wants in a single
    invocation of the ISPAQ top level script.

    After processing the preferences file, the list of internal properties
    will include at least:
     * requested_starttime -- ISO 8601 formatted start time for each seismic signal
     * requested_endtime -- ISO 8601 formatted end time for each seismic signal
     * requested_metric_set -- alias for a list of metrics in the preferences file
     * requested_sncl_set -- alias for a list of SNCLs in the preferences file
     * metric_sets -- dictionary of available metric sets
     * sncl_sets -- dictionary of available sncl sets
     * event_url -- resource to use for event metadata
     * station_url -- resource to use for station metadata
     * dataselect_url -- resource to use for seismic data

    Think of the initialization of the UserRequest object as the work of a lower
    level front desk person who is taking guest information from a handwritten
    request (preferences file) and phone call (command line arguments) and
    transcribing that information onto a standard form that the Concierge keeps
    for each guest. (Each unique invocation of this script is a new 'guest'.)

    It is the job of the Concierge class to use the information in the UserRequest
    to simplify access to data and metadata when requested by downstream
    business logic code.
    """
    def __init__(self,
                 args=None,
                 json_representation=None, dummy=False,
                 logger=None):
        """
        Creates a UserRequest object.

        TODO:  More documentation for __init__?

        .. rubric:: Example

        TODO:  Generate doctest examples by loading from json?
        """

        # Save args

        self.args = args

        #     Initialize a dummy object     -----------------------------------
        
        logger.debug("User request initialization")
 
        if dummy:
            # Information coming in from the command line
            self.requested_starttime = UTCDateTime("2002-04-20")
            self.requested_endtime = UTCDateTime("2002-04-21")
            self.requested_metric_set = 'dummy_metric_set'
            self.requested_sncl_set = 'dummy_sncl_set'
            # Metric and SNCL information from the preferences file
            self.metrics = ['sample_min', 'sample_rms']
            self.sncls = ['US.OXF..BH?']
            # Data access information from the preferences file
            self.event_url = "USGS"
            self.station_url = "IRIS"
            self.dataselect_url = "IRIS"
            # Metric functions determined by querying the R package
            self.invalid_metrics = None
            self.function_by_logic = {'simple': {'basicStats': {'businessLogic': 'simple',
                                                                'elementNames': ['value'],
                                                                'fullDay': True,
                                                                'metrics': ['sample_min', 'sample_rms'],
                                                                'outputType': 'GeneralValue',
                                                                'speed': 'fast',
                                                                'streamCount': 1}}}
            self.preferences = {'plot_output_dir': '.',
                                'csv_output_dir': '.',
                                'sigfigs': 6,
                                'sncl_format': 'N.S.L.C'}

        #     Initialize from JSON     ----------------------------------------
        
        elif json_representation is not None:
            # Load json dictionary from file (or string)
            try:
                with open(os.path.expanduser(json_representation), 'r') as infile:
                    json_dict = json.load(infile)
            except IOError:
                json_dict = json.loads(json_representation)

            # Information coming in from the command line
            self.requested_starttime = UTCDateTime(json_dict['requested_starttime']["timestamp"])
            self.requested_endtime = UTCDateTime(json_dict['requested_endtime']["timestamp"])
            self.requested_metric_set = json_dict['requested_metric_set']
            self.requested_sncl_set = json_dict['requested_sncl_set']
            # Metric and SNCL information from the preferences file
            self.metrics = json_dict['metrics']
            self.sncls = json_dict['sncls']
            # Data access information from the preferences file
            self.event_url = json_dict['event_url']
            self.station_url = json_dict['station_url']
            self.dataselect_url = json_dict['dataselect_url']
            # Metric functions determined by querying the R package
            self.invalid_metrics = json_dict['invalid_metrics']
            self.function_by_logic = json_dict['function_by_logic']

            # Additional metadata for local access
            self.resp_dir = None   # resp_dir is optional for activating local evalresp on RESP files
            if 'resp_dir' in json_dict:
                self.resp_dir = json_dict['resp_dir'] 

            if 'sncl_format' in json_dict:
                self.sncl_format = json_dict['sncl_format']

        #     Initialize from arguments       ---------------------------------

        else:
            # start and end times
            try:
                self.requested_starttime = UTCDateTime(args.starttime)
            except Exception as e:
                logger.critical("Invalid start time %s" % args.starttime)
                raise SystemExit

            if args.endtime is None:
                self.requested_endtime = self.requested_starttime + (24*60*60)
            else:
                try:
                    self.requested_endtime = UTCDateTime(args.endtime)
                except Exception as e:
                    logger.critical("Invalid end time %s" % args.endtime)
                    raise SystemExit

            # metric and sncl sets
            self.requested_metric_set = args.metrics
            self.requested_sncl_set = args.stations

            # url entries
            self.preferences_file = args.preferences_file
            self.station_url = args.station_url
            self.dataselect_url = args.dataselect_url
            self.event_url = args.event_url
            self.resp_dir = args.resp_dir
            self.csv_output_dir = args.resp_dir
            self.plot_output_dir = args.plot_output_dir
            self.sncl_format = args.sncl_format
            self.sigfigs = args.sigfigs

            #     Load preferences from file      -----------------------------

            # Metric and SNCL information from the preferences file
            metric_sets, sncl_sets, data_access, preferences = {}, {}, {}, {}
            currentSection = None
            multiValue = False

            if self.preferences_file is None:
                self.preferences_file=os.path.expanduser('./preference_files/default.txt')
            elif (not os.path.isfile(self.preferences_file)):
                logger.critical("Cannot find preference file %s" % self.preferences_file)
                raise SystemExit

            if os.path.isfile(self.preferences_file): 
                with open(self.preferences_file,"r") as preferences_file:
                    for line in preferences_file:  # parse file
                        line = line.split('#')[0].strip()  # remove comments
                        if line.lower() == "metrics:":  # metric header
                            currentSection = metric_sets
                            multiValue = True
                        elif line.lower() in ['sncls:','station_sncls:','stations:']:
                            currentSection = sncl_sets
                            multiValue = True
                        elif line.lower() == "data_access:":
                            currentSection = data_access
                            multiValue = False
                        elif line.lower() == "preferences:":
                            currentSection = preferences
                            multiValue = False
                        elif currentSection is not None:  # line following header
                            entry = line.split(':',1)
                            if len(entry) <= 1:  # empty line
                                name, values = None, None
                                continue
                            else:  # non-empty line
                                name = entry[0]
                                # check for key with empty value entry, implies optional or default, set value to None in array
                                values = None
                                if name is not None and len(entry) > 1:             # we have a value or set of comma separated values
                                    values = entry[1].strip().split(',')
                                    values = [value.strip() for value in values]
                                    values = filter(None, values)  # remove empty strings -- TODO: this can cause index out of range errors on empty entries
                                        
                            # attempt robust assignment of name to value(s) -- currentSection is the current dictionary of interest
                            if name is None:  # sanity check
                                continue
                            if values is None or len(values) == 0:
                                currentSection[name] = None  # for optional values
                            elif multiValue:
                                currentSection[name] = values
                            else:
                                currentSection[name] = values[0]
            else:
                logger.warning("Cannot find preference file %s, continuing with program defaults" % self.preferences_file)
                        
            # Check for special keyword to exit after loading preferences
            # Be sure to save object instance variables needed from the preference files
            pref_keyword = "LOAD_PREFS_ONLY"
            if pref_keyword in args.metrics:
                self.metric_sets = metric_sets
                self.sncl_sets = sncl_sets
                self.data_access = data_access
                self.preferences = preferences
                return
            
            # Check for missing Data_Access values

            if self.dataselect_url is None:
                if os.path.isfile(self.preferences_file):
                    if 'dataselect_url' not in data_access.keys():
                        logger.critical("Preference file is missing Data_Access: dataselect_url entry.")
                        raise SystemExit
                    if data_access['dataselect_url'] is None:
                        logger.critical("Preference file Data_Access: dataselect_url is not specified.")
                        raise SystemExit
                    else:
                        self.dataselect_url = data_access['dataselect_url']
                else:
                    logger.critical("Reading user input or preferences: no dataselect_url found")
                    raise SystemExit

            if self.station_url is None:
                if 'station_url' in data_access.keys():
                    self.station_url = data_access['station_url']

            if self.event_url is None:
                if 'event_url' in data_access.keys():
                    self.event_url = data_access['event_url']                   

            if self.resp_dir is None:
                if 'resp_dir' in data_access:
                    self.resp_dir = data_access['resp_dir']

            # assign station and metrics aliases 
            try:
                self.metrics = metric_sets[self.requested_metric_set]  # list assignment
            except KeyError as e:
                # assign indicated metric anyway and we will perform a validation check
                logger.debug('Explicit metric detected %s' % e)
                self.metrics = self.requested_metric_set.split(',')  # allow for comma-separated entries

            try:
                self.sncls = sncl_sets[self.requested_sncl_set]  # list assignment
            except KeyError as e:
                # a non-matching station alias might be an actual SNCL name
                # instead of a preferences alias
                logger.debug('Explicit SNCL detected %s' % e)
                reg_expr = '([a-zA-Z0-9_*?]+?\.){2}[a-zA-Z0-9_*?]*?\.[a-zA-Z0-9_*?]+?'
                if re.search(reg_expr, self.requested_sncl_set):  # best guess for validity
                    self.sncls = self.requested_sncl_set.split(',')  # allow for comma-separated entries
                else:
                    logger.critical('Invalid station parameter: %s' % e)
                    raise SystemExit
            
            #     Add individual preferences     ------------------------------
            
            if self.plot_output_dir is None:
                if preferences.has_key('plot_output_dir'):
                    self.plot_output_dir = os.path.abspath(os.path.expanduser(preferences['plot_output_dir']))
                else:
                    self.plot_output_dir = os.path.abspath('.')
            if self.csv_output_dir is None:
                if preferences.has_key('csv_output_dir'):
                    self.csv_output_dir = os.path.abspath(os.path.expanduser(preferences['csv_output_dir']))
                else:
                    self.csv_output_dir = os.path.abspath('.')
            if self.sigfigs is None:
                if preferences.has_key('sigfigs'):
                    self.sigfigs = preferences['sigfigs']
                else:
                    self.sigfigs = 6
            if self.sncl_format is None:
                if preferences.has_key('sncl_format'):
                    self.sncl_format = preferences['sncl_format']
                else:
                    self.sncl_format = "N.S.L.C"

            sncl_expr = re.compile('[SNCL][\.][SNCL][\.][SNCL][\.][SNCL]')
            if (not re.match(sncl_expr, self.sncl_format)):
                logger.critical('sncl_format %s is not valid' % self.sncl_format)
                raise SystemExit

            #     Find required metric functions     --------------------------

            # Obtain a dictionary from ispaq.irismustangmetrics of the following form:
            # {metric_function_1: <various metadata including list of metrics>}
            # We will restructure this dictionary, modifying the list of metrics
            # generated by each function to include only those that were requested.
            # The final form will have the following hierarchy:
            #   business_logic > function_name > metric name

            # Get the dictionary from the R package
            default_function_dict = irismustangmetrics.function_metadata()

            # Determine which functions and logic types are required
            valid_function_names = set()
            valid_logic_types = set()
            
            # Keep track of valid metrics (typos might cause some to not be found)
            valid_metrics = set()

            # Loop over all default functions to see if any associated metrics were requested
            for function_name in default_function_dict:
                default_function = default_function_dict[function_name]
                for metric in self.metrics:
                    if metric in default_function['metrics']:
                        valid_function_names.add(function_name)
                        valid_logic_types.add(default_function['businessLogic'])
                        valid_metrics.add(metric)

            # Warn of invalid metrics
            invalid_metrics = set(self.metrics).difference(valid_metrics)
            if len(invalid_metrics):
                logger.warning('The following metric names are invalid and were ignored: ' + str(list(invalid_metrics)))
            if not len(valid_metrics):
                logger.critical('No valid metrics exist')
                raise SystemExit

            # check for empty sncl and metrics entries
            if self.sncls is None or len(set(self.sncls)) == 0:
                logger.critical('No valid stations exist')
                raise SystemExit
            if self.metrics is None or len(set(self.metrics)) == 0:
                logger.critical('No valid metrics exist')
                raise SystemExit
            
            # Check for metrics that may require a more recent version of ISPAQ --------------------
            ispq = currentispaq()
            versionMetric = []

            for function_name in valid_function_names:
                default_function = default_function_dict[function_name]
                bLogic = default_function['businessLogic']
                if bLogic not in ispq:    
                    for metric_name in set(default_function['metrics']).intersection(valid_metrics):
                        versionMetric.append(metric_name)
                else:
                    if function_name not in ispq[bLogic]:
                        for metric_name in set(default_function['metrics']).intersection(valid_metrics):
                            versionMetric.append(metric_name)
 
            if len(versionMetric):
                logger.warning("The following metrics will not run with this version of ISPAQ: " + str([str(x) for x in versionMetric]))

            # Now reconstruct the reorganized function_by_logic dictionary with only 
            # user requested logic types, functions and metrics that can run on this ISPAQ version
            function_by_logic = {}
            for logic_type in set(ispq).intersection(valid_logic_types):
                function_by_logic[logic_type] = {}
                for function_name in set(ispq[logic_type]).intersection(valid_function_names):
                    function = default_function_dict[function_name]
                    if function['businessLogic'] == logic_type:
                        # Modify the metric names associated with this function
                        function['metrics'] = list( set(function['metrics']).intersection(valid_metrics) )
                        function_by_logic[logic_type][function_name] = function

            if not len(function_by_logic):
                logger.critical('No valid metrics exist')
                raise SystemExit

            # Assign the invalid metrics and restructured function_by_logic dictionary
            self.invalid_metrics = list(invalid_metrics)
            self.function_by_logic = function_by_logic


    def json_dump(self, file_loc=None, pretty=False):
        """
        Dump a dictionary of UserRequest properties as a json string.
        
        Does not catch IOError if file_loc is invalid
        :param file_loc: location to write json
        :return: json string representation of internal properties

        >>> u = UserRequest(dummy=True)
        >>> output = u.json_dump()
        >>> output #doctest: +ELLIPSIS
        '{"args": null, "dataselect_url": "IRIS", "event_url": "IRIS", "function_by_logic": {"simple": {"basicStats":...'
        >>> s = UserRequest(json_representation=output)
        >>> s.json_dump() #doctest: +ELLIPSIS
        '{"args": null, "dataselect_url": "IRIS", "event_url": "IRIS", "function_by_logic": {"simple": {"basicStats":...'
        """

        if pretty:
            json_string = json.dumps(self, default=lambda o: o.__dict__,
                                     sort_keys=True, indent=4, separators=(',', ': '))
        else:
            json_string = json.dumps(self, default=lambda o: o.__dict__,
                                     sort_keys=True)

        if file_loc is not None:
            with open(os.path.expanduser(file_loc), 'w') as outfile:
                outfile.write(json_string)
        return json_string

    def __str__(self):
        return self.json_dump()
        

if __name__ == '__main__':
    import doctest
    doctest.testmod(exclude_empty=True)
