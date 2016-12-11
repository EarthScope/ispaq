#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-


"""Convenience wrapper for running ispaq directly from source tree."""

from __future__ import (absolute_import, division, print_function)

import warnings
warnings.simplefilter(action = "ignore", category = FutureWarning)

from ispaq.ispaq import main

if __name__ == '__main__':
    main()
