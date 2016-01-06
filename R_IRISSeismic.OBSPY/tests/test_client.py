# -*- coding: utf-8 -*-
"""
### The obspy.clients.iris.client test suite.
The R_IRISSeismic test suite.
"""
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
from future.builtins import *  # NOQA @UnusedWildImport

import os
import unittest

import numpy as np

from obspy.core.utcdatetime import UTCDateTime
from obspy.core.util import NamedTemporaryFile
### from obspy.clients.iris import Client
from obspy.fdsn import Client


class ClientTestCase(unittest.TestCase):
    """
    Test cases for obspy.clients.iris.client.Client.
    """
    def setUp(self):
        # directory where the test files are located
        self.path = os.path.dirname(__file__)

    def test_timeseries(self):
        """
        Tests timeseries Web service interface.

        Examples are inspired by http://www.iris.edu/ws/timeseries/.
        """
        ### client = Client()
        client = Client("IRIS")
        
        # 1
        t1 = UTCDateTime("2005-001T00:00:00")
        t2 = UTCDateTime("2005-001T00:01:00")
        # no filter
        st1 = client.timeseries("IU", "ANMO", "00", "BHZ", t1, t2)
        # instrument corrected
        st2 = client.timeseries("IU", "ANMO", "00", "BHZ", t1, t2,
                                filter=["correct"])
        # compare results
        self.assertEqual(st1[0].stats.starttime, st2[0].stats.starttime)
        self.assertEqual(st1[0].stats.endtime, st2[0].stats.endtime)
        self.assertEqual(st1[0].data[0], 24)
        self.assertAlmostEqual(st2[0].data[0], -2.8373747e-06)


def suite():
    return unittest.makeSuite(ClientTestCase, 'test')


if __name__ == '__main__':
    unittest.main(defaultTest='suite')
