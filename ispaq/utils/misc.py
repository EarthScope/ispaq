from __future__ import (absolute_import, division, print_function,
                        unicode_literals)


def statuswrap(function, arg_to_print, exception, *arg):
    """helps track progress when using apply"""
    try:
        v = function(*arg)
        print('   %s Done' % arg[arg_to_print])        
        return v
    except exception:
        print('   %s Failed' % arg[arg_to_print])

def check_negative(value):
    import argparse
    ivalue = int(value)
    if ivalue < 0:
        raise argparse.ArgumentTypeError("%s is an invalid positive int value" % value)
    return ivalue
