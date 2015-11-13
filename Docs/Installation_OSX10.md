# Installation Instructions for OSX 10.x

This document provides [ObsPy](https://github.com/obspy/obspy/wiki) installation instructions
that have been tested on the following Macintosh operating systems:

 * OSX 10.10
 

## Xcode ##

You must have Xcode installed. This can be installed from the AppStore.


## Anaconda ##

Anaconda is the python package manager used by ObsPy. We will follow the
[Miniconda installation instructions](http://conda.pydata.org/docs/install/quick.html):

 1. download the [python 2.7 miniconda OSX install script](https://repo.continuum.io/miniconda/Miniconda-latest-MacOSX-x86_64.sh)
 1. `bash Miniconda-latest-MacOSX-x86_64.sh`
 1. accept default arguments
 1. test by typing `conda`
 

## ObsPy ##

Following the [ObsPy Anaconda installation instructions](https://github.com/obspy/obspy/wiki/Installation-via-Anaconda),
all we need to do is:

 1. `conda install -c obspy obspy`
 1. accept installation of new packages
 1. test by typing `obspy-runtests` (this will take a while)

*Note:* this mail fail with warnings about "... distribution was not found and is required ..."

If this happens, just install the missing packages as in the following examples:

`conda install numpy`  
`conda install matplotlib`  
`conda install nose`  

----

### ObsPy test results ###

One one machine running OSX 10.10.5 we got 1/1195 failures:

`FAIL: test_coincidenceTriggerWithSimilarityChecking (obspy.signal.tests.test_trigger.TriggerTestCase)`


## rpy2 and R ##

To install both R and rpy2 using Anaconda, all we need to do is this:

 1. conda install -c https://conda.anaconda.org/r rpy2
 1. accept installation of new packages

