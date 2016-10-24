# ISPAQ

*IRIS System for Portable Assessment of Quality*

# Background

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

# Installation

## Download the Source Code

You must first have ```git``` installed your system. Once you do, just:

```
git clone https://github.com/iris-edu/ispaq.git
```

Onced finished, ```cd ispaq``` before setting up the Anaconda environment.

## Install the Anaconda Environment

[Anaconda](https://www.continuum.io/why-anaconda) is quickly becoming the *defacto*
package manager for scientific applications written python or R. The following instructions
assume that you have installed [Miniconda](http://conda.pydata.org/miniconda.html) for
your system.

We will use conda to simplify installation and ensure that all dependencies
are installed with compatible verions.

By setting up a [conda virual environment](http://conda.pydata.org/docs/using/envs.html),
we assure that our ISPAQ installation is entirely separate from any other installed software.

### Alternative 1) Creating an environment from a 'spec' file

This method does everything at once.

```
conda create -n ispaq --file ispaq-explicit-spec-file.txt
source activate ispaq
```

See what is installed in our (ispaq) environment with:

```
conda list
...
```

Now install the IRIS R packages:

```
R CMD install seismicRoll_1.1.2.tar.gz 
R CMD install IRISSeismic_1.3.5.tar.gz
R CMD install IRISMustangMetrics_2.0.0.tar.gz 
```

### Alternative 2) Creating an environment by hand

This method requires more user intput but lets you see what is being installed.

```
conda create --name ispaq python=2.7
source activate ispaq
conda install pandas=0.18.1
conda install -c conda-forge obspy=1.0.2
conda install -c r r=3.2.2
conda install -c r r-devtools=1.9.1
conda install -c r r-rcurl=1.95_4.7
conda install -c r r-xml=3.98_1.3 
conda install -c r r-dplyr=0.4.3
conda install -c r r-tidyr=0.3.1
conda install -c r r-quadprog=1.5.5
conda install -c bioconda r-signal=0.7.6
conda install -c bioconda r-pracma=1.8.8
conda install -c r rpy2=2.7.0
```

See what is installed in our (ispaq) environment with:

```
conda list
...
```

Now install the IRIS R packages:

```
R CMD install seismicRoll_1.1.2.tar.gz 
R CMD install IRISSeismic_1.2.3.tar.gz
R CMD install IRISMustangMetrics_1.2.5.tar.gz 
```

# First use

Every time you use ISPAQ you must ensure that you are running in the proper Anaconda
environment. If you followed the instructions above you only need to:

```
source activate ispaq
```

after which your prompt should begin with ```(ispaq) ```.

A list of command line options is available with the ```--help``` flag:

```
(ispaq) $ ./ispaq-runner.py --help
usage: ispaq-runner.py [-h] [-V] [--starttime STARTTIME] [--endtime ENDTIME]
                       [-M METRICS] [-S SNCLS] [-P PREFERENCES_FILE]
                       [--log-level {DEBUG,INFO,WARNING,ERROR,CRITICAL}] [-A]
                       [-U]

ispaq.ispaq: provides entry point main().

optional arguments:
  -h, --help            show this help message and exit
  -V, --version         show program's version number and exit
  --starttime STARTTIME
                        starttime in ISO 8601 format
  --endtime ENDTIME     endtime in ISO 8601 format
  -M METRICS, --metrics METRICS
                        name of metric to calculate
  -S SNCLS, --sncls SNCLS
                        Network.Station.Location.Channel identifier (e.g.
                        US.OXF..BHZ)
  -P PREFERENCES_FILE, --preferences-file PREFERENCES_FILE
                        location of preference file
  --log-level {DEBUG,INFO,WARNING,ERROR,CRITICAL}
                        log level printed to console
  -A, --append          append to TRANSCRIPT file rather than overwriting
  -U, --update-r        report on R package updates
(ispaq) $ 
```

### Preference files

The ISPAQ system is designed to be configurable through the user of *preference files*.
These are located in the ```preference_files/``` directory.  Not surprisingly, the default
preference file is ```preference_files/default.txt``. This file is self describing
with the following comments in the header:

```
# Preferences fall into four categories:
#  * Metrics -- aliases for user defined combinations of metrics
#  * SNCLs -- aliases for user defined combinations of SNCL patterns
#  * Data_Access -- FDSN web services or local files
#  * Preferences -- additional user preferences
#
# This file is in a very simple and somewhat forgiving format.  After
# each category heading, all lines containing a colon will be interpreted
# as key:value and made made available to ISPAQ.
#
# Text to the right of `#` are comments and are ignored by the parser

# Example invocations that use these default preferences:
#
#   ispaq-runner.py -M basicStats -S basicStats --starttime 2010-04-20 --log-level INFO -A
#   ispaq-runner.py -M gaps -S gaps --starttime 2013-01-05 --log-level INFO -A
#   ispaq-runner.py -M spikes -S spikes --starttime 2013-01-03 --log-level INFO -A
#   ispaq-runner.py -M STALTA -S STALTA --starttime 2013-06-02 --log-level INFO -A
#   ispaq-runner.py -M SNR -S SNR --starttime 2013-06-02 --log-level INFO -A
#   ispaq-runner.py -M PSD -S PSD --starttime 2011-05-18 --log-level INFO -A
#   ispaq-runner.py -M PDF -S PDF --starttime 2013-06-01 --log-level INFO -A
#   ispaq-runner.py -M crossTalk -S crossTalk --starttime 2013-09-21 --log-level INFO -A
#   ispaq-runner.py -M pressureCorrelation -S pressureCorrelation --starttime 2013-05-02 --log-level INFO -A
#   ispaq-runner.py -M crossCorrelation -S crossCorrelation --starttime 2011-01-01 --log-level INFO -A
#   ispaq-runner.py -M orientationCheck -S orientationCheck --starttime 2015-11-24 --log-level INFO -A
#   ispaq-runner.py -M transferFunction -S transferFunction --starttime 2012-10-03 --log-level INFO -A
```

### Output files

ISPAQ will always create a log file named ```ISPAQ_TRANSCRIPT.log``` to record all actions taken
and all logging messages generated during processing.

Results of metrics calculations will be written to .csv files using the following naming scheme:

*MetricSet*\_*SNCLSet*\_*date*\__*businessLogic*.csv

Additional files are created by the ```PSD``` and ```PDF``` metrics. Running any ```PSD```
metrics will also generate both corrected PSDs and PDFs in files named:

* *MetricSet*\_*SNCLSet*\_*date*\_*SNCL*\__correctedPSD.csv
* *MetricSet*\_*SNCLSet*\_*date*\_*SNCL*\__PDF.csv

while asking for the ```PDF``` will generate PDF images as:

* *SNCL*\.*JulianDate*\_PDF.png

### Command line invocation

Example invocations are found  in the ```EXAMPLES``` file. 

You can modify the information printed to the console by modifying the ```--log-level```.
To see detailed progress information use ```--log-level DEBUG```. To hide everything other
than an outright crash use ```--log-level CRITICAL```.

The following example demonstrates what will should see. 

```
(ispaq) $ ispaq-runner.py -M basicStats -S basicStats --starttime 2010-04-20 --log-level INFO
2016-08-26 15:50:43 - INFO - Running ISPAQ version 0.7.6 on Fri Aug 26 15:50:43 2016

/Users/jonathancallahan/miniconda2/envs/ispaq/lib/python2.7/site-packages/matplotlib/font_manager.py:273: UserWarning: Matplotlib is building the font cache using fc-list. This may take a moment.
  warnings.warn('Matplotlib is building the font cache using fc-list. This may take a moment.')
2016-08-26 15:51:02 - INFO - Calculating simple metrics for 3 SNCLs.
2016-08-26 15:51:02 - INFO - 000 Calculating simple metrics for IU.ANMO.00.BH1
2016-08-26 15:51:04 - INFO - 001 Calculating simple metrics for IU.ANMO.00.BH2
2016-08-26 15:51:07 - INFO - 002 Calculating simple metrics for IU.ANMO.00.BHZ
2016-08-26 15:51:09 - INFO - Writing simple metrics to basicStats_basicStats_2010-04-20__simpleMetrics.csv.

2016-08-26 15:51:09 - INFO - ALL FINISHED!
(ispaq) $
```

> Note: Please ignore the warning message from matplotlib until we figure out how to suppress it.

----


