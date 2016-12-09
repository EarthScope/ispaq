# ISPAQ - IRIS System for Portable Assessment of Quality

ISPAQ is a python client that allows seismic data scientists and instrumentation operators
to run data quality metrics on their own workstation, using much of same code base as is
used in IRIS's MUSTANG data quality web service.

Users have the ability to create personalized _preference files_ that list combinations
of station specifiers and statistical metrics of interest, such that they can be run
repeatedly over data from many different time periods.

ISPAQ offers the option for access to FDSN Web Services to get raw data and metadata directly
from selected data centers supporting the FDSN protocol.  Alternately, users can ready local files
and metadata on their own workstations, possibly sourced directly from instrumentation, and construct
on-the-spot data quality analyses on that data.

Output is provided in csv format for tabular metrics, and Probability Density Functions can be
plotted to PNG image files.

The business logic for MUSTANG metrics is emulated through ObsPy and custom Python code and the
core calculations are performed using the same R packages as used by MUSTANG.  Currently, only
SEED formatted data and StationXML metadata is supported as source seismogram material.  RESP files
and FDSN Web Service event files are also used in some situations.

# Background

[IRIS](http://www.iris.edu/hq/) (Incorporated Research Institutions for Seismology)
 has developed a comprehensive quality assurance system called
[MUSTANG](http://service.iris.edu/mustang/).

The MUSTANG system was built to operate at the IRIS DMC and is not generally portable. 
The key MUSTANG component is the Metric Calculators, and those were always
intended to be shared.  Whereas the results of MUSTANG calculations are stored in a database, and
provided to users via web services, ISPAQ is intended to reproduce the process of calculating these
metrics from the source data, such that results can be verified and alternate data sources not
available in MUSTANG can be processed at the user's initiative.

IRIS currently has close to 50 MUSTANG algorithms that calculate metrics, most 
written in R, that are now publicly available in the CRAN repository under the name 
[IRISMustangMetrics](http://cran.r-project.org/).  ISPAQ comes with the latest version of these packages
available in CRAN and we provide an update capability in ISPAQ to allow users to seamlessly upgrade
their R packages as IRIS provides them.

The R package IRISMustangMetrics cannot include workflow and data selection
business logic implemented at scale in MUSTANG, as much of this code is non-portable.  However, it
is the goal of ISPAQ to provide a similar set of business logic in Python, such that the end result
is identical or very similar to the results you will see in MUSTANG.  The end result is a lightweight
and portable version of MUSTANG that users are free to leverage on their own hardware.

# Installation

ISPAQ must be installed on the user's system using very reliable tools for package transfer.  ISPAQ is being
distributed through _GitHub_, via IRIS's public repository.  You will use a simple command to get a copy of
the latest stable release.  In addition, you will use the _miniconda_ python package manager to create a
customized environment designed to run ISPAQ properly.  This will include an localized installation of ObsPy and R.
Just follow the steps below to begin running ISPAQ.

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

### Alternative 1 for MacOSX ) Creating an environment from a 'spec' file

This method does everything at once.

```
conda create -n ispaq --file ispaq-explicit-spec-file.txt
source activate ispaq
```

(note: if `source activate ispaq` does not work because your shell is csh/tcsh instead of bash
you will need to add the ispaq environment to your PATH in the terminal window that you are using.
e.g., `setenv PATH ~/miniconda2/envs/ispaq/bin:$PATH`)

See what is installed in our (ispaq) environment with:

```
conda list
...
```

Now install the IRIS R packages:

```
R CMD INSTALL seismicRoll_1.1.2.tar.gz 
R CMD INSTALL IRISSeismic_1.3.9.tar.gz
R CMD INSTALL IRISMustangMetrics_2.0.2.tar.gz 
```

### Alternative 2 for MacOSX or Linux ) Creating an environment by hand

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
conda install -c r r-quadprog=1.5.5
conda install -c bioconda r-signal=0.7.6
conda install -c bioconda r-pracma=1.8.8
conda install -c bioconda rpy2=2.7.8
```

(note: if `source activate ispaq` does not work because your shell is csh/tcsh instead of bash
you will need to add the ispaq environment to your PATH in the terminal window that you are using.
e.g., `setenv PATH ~/miniconda2/envs/ispaq/bin:$PATH`)

See what is installed in our (ispaq) environment with:

```
conda list
...
```

Now install the IRIS R packages:

```
R CMD INSTALL seismicRoll_1.1.2.tar.gz 
R CMD INSTALL IRISSeismic_1.3.9.tar.gz
R CMD INSTALL IRISMustangMetrics_2.0.2.tar.gz 
```

# First use

Every time you use ISPAQ you must ensure that you are running in the proper Anaconda
environment. If you followed the instructions above you only need to:

```
source activate ispaq
```

after which your prompt should begin with ```(ispaq) ```.

(note: if you are using a csh/tcsh shell there will be no prompt change)

A list of command line options is available with the ```--help``` flag:

```
(ispaq) $ ./run_ispaq.py --help
usage: run_ispaq.py [-h] [-V] [--starttime STARTTIME] [--endtime ENDTIME]
                    [-M METRICS] [-S STATIONS] [-P PREFERENCES_FILE]
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
                        metric alias, defined in preference file
  -S STATIONS, --stations STATIONS
                        stations alias, defined in preference file
  -P PREFERENCES_FILE, --preferences-file PREFERENCES_FILE
                        location of preference file
  --log-level {DEBUG,INFO,WARNING,ERROR,CRITICAL}
                        log level printed to console
  -A, --append          append to TRANSCRIPT file rather than overwriting
  -U, --update-r        check CRAN for more recent IRIS Mustang R package
                        versions
```

When calculating metrics, valid arguments for -M, -S, and --starttime must be provided. 
If -P is not provided, ISPAQ uses the default preference file located at ispaq/preference_files/default.txt.
If --log-level is not specified, the default log-level is INFO.

When --starttime is invoked without --endtime, metrics are run for a single day. Metrics that are defined  
as daylong metrics (24 hour window, see metrics documentation at http://services.iris.edu/mustang/measurements/1)
will be calculated for the time period 00:00:00-23:59:59.9999. An endtime of YYYY-DD-MM is interpreted as 
YYYY-DD-MM 00:00:00 so that e.g., --starttime=2016-01-01 --endtime=2016-01-02 will calculate one day of metrics. 
When an endtime greater than one day is requested, metrics will be calculated for multiple single days. 

The option -U should be used alone. No metrics are calculated when this option is invoked.

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
#   run_ispaq.py -M basicStats -S basicStats --starttime 2010-04-20 --log-level INFO -A
#   run_ispaq.py -M gaps -S gaps --starttime 2013-01-05 --log-level INFO -A
#   run_ispaq.py -M spikes -S spikes --starttime 2013-01-03 --log-level INFO -A
#   run_ispaq.py -M STALTA -S STALTA --starttime 2013-06-02 --log-level INFO -A
#   run_ispaq.py -M SNR -S SNR --starttime 2013-06-02 --log-level INFO -A
#   run_ispaq.py -M PSD -S PSD --starttime 2011-05-18 --log-level INFO -A
#   run_ispaq.py -M PDF -S PDF --starttime 2013-06-01 --log-level INFO -A
#   run_ispaq.py -M crossTalk -S crossTalk --starttime 2013-09-21 --log-level INFO -A
#   run_ispaq.py -M pressureCorrelation -S pressureCorrelation --starttime 2013-05-02 --log-level INFO -A
#   run_ispaq.py -M crossCorrelation -S crossCorrelation --starttime 2011-01-01 --log-level INFO -A
#   run_ispaq.py -M orientationCheck -S orientationCheck --starttime 2015-11-24 --log-level INFO -A
#   run_ispaq.py -M transferFunction -S transferFunction --starttime 2012-10-03 --log-level INFO -A
```

### Output files

ISPAQ will always create a log file named ```ISPAQ_TRANSCRIPT.log``` to record all actions taken
and all logging messages generated during processing.

Results of metrics calculations will be written to .csv files using the following naming scheme:

*MetricSet*\_*StationSet*\_*date*\__*businessLogic*.csv

or

*MetricSet*\_*StationSet*\_*startdate*\_*enddate*\_*businessLogic*.csv

where businessLogic corresponds to which ispaq script is invoked:
 
simpleMetrics -> ispaq/simple_metrics.py  (most metrics that do not depend on metadata or event information)
SNRMetrics -> ispaq/SNR_metrics.py        (sample_snr)
PSDMetrics -> ispaq/PSD_metrics.py        (pct_above_nhnm, pct_below_nlnm, dead_channel_exp/lin/gsn)
crossTalkMetrics -> ispaq/crossTalk_metrics.py                       (cross_talk)
pressureCorrelationMetrics -> ispaq/pressureCorrelation_metrics.py   (pressure_effects)
crossCorrelationMetrics -> ispaq/crossCorrelation_metrics.py         (polarity_check)
orientationCheckMetrics -> ispaq/orientationCheck_metrics.py         (orientation_check)
transferMetrics -> ispaq/transferFunction_metrics.py                 (transfer_function)

The MetricSet PDFtext (metrics psd_corrected, pdf_text) will generate corrected PSDs and PDFs in files named:

* *MetricSet*\_*StationSet*\_*date*\_*SNCL*\__correctedPSD.csv
* *MetricSet*\_*StationSet*\_*date*\_*SNCL*\__PDF.csv

while asking for the MetricSet ```PDF``` (metric pdf_plot) will generate PDF plot images as:

* *SNCL*\.*JulianDate*\_PDF.png

### Command line invocation

Example invocations are found  in the ```EXAMPLES``` file. 

You can modify the information printed to the console by modifying the ```--log-level```.
To see detailed progress information use ```--log-level DEBUG```. To hide everything other
than an outright crash use ```--log-level CRITICAL```.

The following example demonstrates what will should see. 

```
(ispaq) $ run_ispaq.py -M basicStats -S basicStats --starttime 2010-04-20 --log-level INFO
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

> Note: Please ignore the warning message from matplotlib until we figure out how to suppress it. It will only occur on first use. 

### Using Local Data Files

1. data directory
2. data format, miniSEED and StationXML
3. `dataselect` script
4. what happens if data is not in the correct file
5. lack of flag metrics, obspy

