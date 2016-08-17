# ISPAQ

*IRIS System for Portable Assessment of Quality*

## Background

[IRIS](http://www.iris.edu/hq/) (Incorporated Research Institutions for Seismology)
 has developed a comprehensive quality assurance system called
[MUSTANG](http://service.iris.edu/mustang/).

MUSTANG consists of several components:

 * a scheduling system that controls when metrics are computed on specific pieces of the IRIS seismic archive
 * a database to store results of those calculations
 * a system that determines when metrics should be refreshed due to changes in metadata, time series data, or algorithmic implementation
 * several dozen metric calculators that generate the QA related statistics

The MUSTANG system was built to operate at the IRIS DMC and is not portable. 
However, the key MUSTANG component is the Metric Calculators, and those were always
intended to be shared. For seismic networks or experiments that do not have their 
data managed by IRIS, we wish to develop an IRIS System for Portable Assessment of 
Quality (ISPAQ). This will be a portable system for data centers or individual 
field investigators to enable localized data quality assessment. ISPAQ will make
use of FDSN web services through which the required information to make the statistical 
calculations can be accessed. Necessarily, the system must be much less complex and 
less automated than the IRIS MUSTANG implementation, but still enables seismic networks
to perform quality assurance on the data from their networks and experiments.

IRIS currently has approximately 50 MUSTANG algorithms that calculate metrics, most 
written in R, that are now publicly available in the CRAN repository under the name 
IRISMustangMetrics. The CRAN repository only contains algorithms written in R 
(and R-compatible compiled code). Other MUSTANG quality metrics that are not written 
in R are not intended to be part of ISPAQ at this time. More metrics will be added 
to the repository in the future. The ISPAQ system must be dynamic, when a new metric 
is included in the CRAN repository, ISPAQ would learn about it automatically and 
enable the execution of the new metric algorithm on a local set of data. R provides 
facilities for this update detection.

## Installation via Anaconda

[Anaconda](https://www.continuum.io/why-anaconda) is quickly becoming the *defacto*
package manager for scientific applications written python or R. The following instructions
assume that you have installed [Miniconda](http://conda.pydata.org/miniconda.html) for
your system.

We will use conda to simplify installation and ensure that all dependencies
are installed with compatible verions.

## Set up a virutal environment for ispaq.

By setting up a [conda virual environment](http://conda.pydata.org/docs/using/envs.html),
we assure that our ISPAQ installation is entirely separate from any other installed software.

```
conda create --name ispaq python=2.7
source activate ispaq
```

See what is installed with:

```
conda list
```

## Install versioned python and R prerequisites

```
conda config --add channels conda-forge
conda install pandas=0.18
conda install obspy=1.0
conda install r=3.2
conda install r-rcurl
```

## Install R package seismicRoll and prerequisites

```
Rscript -e "install.packages('Rcpp', repos='http://cran.fhcrc.org')"
R CMD install 
```

----

## [DEPRECATED] Installing Python Prerequisites

This python application is best installed by using
[virtualenv](https://python-packaging-user-guide.readthedocs.org/en/latest/projects/#virtualenv)
to set up a virtual environment that isolates package dependencies and then using
[pip](https://python-packaging-user-guide.readthedocs.org/en/latest/projects/#pip)
to install packages.

The
[Python Packaging User Guide](https://python-packaging-user-guide.readthedocs.org/en/latest/installing/)
is the closest thing python has to a *definitive* guide to package creation and installation.
That site should be consulted if any of the instructions below do not work

### Installing pip

*Copied from [here](https://python-packaging-user-guide.readthedocs.org/en/latest/installing/#install-pip-setuptools-and-wheel):*

If you have Python 2 >=2.7.9 or Python 3 >=3.4 installed from python.org, you will already have pip and setuptools, but will need to upgrade to the latest version:

On Linux or OS X:

```
pip install -U pip setuptools
```

### Installing virtualenv

*Copied from [here](https://python-packaging-user-guide.readthedocs.org/en/latest/installing/#optionally-create-a-virtual-environment):*

```
pip install virtualenv
```

### Setting up a virtual environment

A virtual environment allows users without super user privileges to set
up a local environment where python packages will be installed and referenced

To set up a virtual environment for python 2.7 in your home directory type
the following on OSX:

```
virtualenv --python=/usr/bin/python2.7 ~/venvpy27
```

To activate the environment type:

```
source ~/venvpy27/bin/activate
```

You can check that your version of python is now coming from this environment 
with:

```
which python
```

### Install python packages

All python prerequisites can be installed with:

```
pip install numpy
pip install obspy
pip install pandas
pip install rpy2
pip install logging
```

## Installing and Running ispaq from Source

If you have downloaded the [ispaq source](https://github.com/mazamascience/ispaq) you can
enter the top level directory and type:

```python setup.py install```

In this same directory you can test the installation with:

```ispaq -M metrics_1 -S sncls_1 --starttime 2010-04-20 --log-level DEBUG```

