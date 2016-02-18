from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
import json
import sys


def preferenceloader(pref_loc):
    """
    Safely loads preference file from the specified location
    :param pref_loc: string file location
    :return: a tuple (metrics, sncls) where each refers to the specified
             sub-dictionary of the JSON file
    """
    try:  # check if file exists
        from os.path import expanduser
        pref_loc = expanduser(pref_loc)
        pref_file = open(pref_loc, 'r')
        print('Loading preferences from %s...' % pref_loc)
        preferences = json.load(pref_file)
    except AttributeError:
        print(sys.exc_info())
        print('No user preferences discovered. Ignoring...\n')
        return None

    try:  # check if file contains custom metrics
        print('   Custom metric sets...', end='  ')
        custom_metric_sets = preferences['MetricAlias']
        print('Done')
    except KeyError:
        custom_metric_sets = None
        print('not found')

    try:  # check if file contains custom sncls
        print('   Custom SNCLs...', end='        ')
        custom_sncl = preferences['SNCLAlias']
        print('Done')
    except KeyError:
        custom_sncl = None
        print('Not found')

    print('Preferences loaded.\n')
    return custom_metric_sets, custom_sncl


def statuswrap(function, *arg):
    v = function(*arg)
    print('   Done')
    return v