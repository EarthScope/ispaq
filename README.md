# ISPAQ - IRIS System for Portable Assessment of Quality

ISPAQ is a Python client that allows seismic data scientists and instrumentation operators to run data 
quality metrics on their own workstation, using much of same code as used in IRIS's 
[MUSTANG](http://service.iris.edu/mustang/) data quality web service. It can be installed on Linux 
and macOS.

Users have the ability to create personalized _preference files_ that list combinations
of station specifiers and statistical metrics of interest, such that they can be run
repeatedly over data from many different time periods. Alternatively, single station specifiers 
and metrics can be specified on the command line for simple runs or for use in shell scripting.

ISPAQ offers the option for access to [FDSN Web Services](http://www.fdsn.org/webservices/) to retrieve 
seismic data and metadata directly from selected data centers supporting the FDSN protocol. Users also 
have the option to read local [miniSEED](http://ds.iris.edu/ds/nodes/dmc/data/formats/seed/) files and 
metadata on their own workstations and construct on-the-spot data quality analyses on that data.

Output is provided in CSV format for tabular metrics. In addition, Probability Density Functions (PDF) 
can be plotted to PNG image files. The PDF plots also include the New High Noise Model and the New Low Noise Model curves [Peterson,1993](https://doi.org/10.3133/ofr93322) and the minimum, maximum, and mode PDF statistics curves.

The business logic for MUSTANG metrics is emulated through [ObsPy](https://github.com/obspy/obspy/wiki) 
and custom Python code and the core calculations are performed using the same R packages as used by 
MUSTANG.


# Background

[IRIS](http://www.iris.edu/hq/) (Incorporated Research Institutions for Seismology) has developed a 
comprehensive quality assurance system called [MUSTANG](http://service.iris.edu/mustang/).

The MUSTANG system was built to operate at the IRIS DMC and is not generally portable. 
However, the key MUSTANG component is the Metric Calculators and these are publicly available. 
While the results of MUSTANG calculations are stored in a database and provided to users via web 
services, ISPAQ is intended to carry out the process of calculating these metrics locally on the 
user's workstation. This has the benefit of allowing users to generate just-in-time metrics on data 
of their choosing, whether stored an FDSN data center or on the user's own data store.

IRIS has over 40 MUSTANG metrics algorithms, most written in R, that are now available in the CRAN 
(Comprehensive R Archive Network) repository under the name [IRISMustangMetrics](http://cran.r-project.org/). 
ISPAQ comes with the latest version of these packages available in CRAN and ISPAQ has an update capability to 
allow users to seamlessly upgrade these R packages as new releases become available.

ISPAQ contains business logic similar to MUSTANG, such that the computed metrics produced are identical 
(or very similar) to the results you will see in MUSTANG. The end result is a lightweight and portable 
version of MUSTANG that users are free to leverage on their own hardware.


#### Questions or comments can be directed to the IRIS DMC Quality Assurance Group at <a href="mailto:dmc_qa@iris.washington.edu">dmc_qa@iris.washington.edu</a>.


# Installation

ISPAQ is distributed through _GitHub_, via IRIS's public repository (_iris-edu_). You will use a ```git``` 
client command to get a copy of the latest stable release. In addition, you will use the ```miniconda``` 
python package manager to create a customized Python environment designed to run ISPAQ properly. This will 
include a localized installation of ObsPy and R.

If running macOS, Xcode command line tools should be installed. Check for existence and install if 
missing:
```
xcode-select --install
```

Follow the steps below to begin running ISPAQ.

## Download the Source Code

You must first have ```git``` installed your system. This is a commonly used source code management system
and serves well as a mode of software distribution as it is easy to capture updates. See the 
[Git Home Page](https://git-scm.com/) to begin installation of git before proceeding further.

After you have git installed, you will download the ISPAQ distribution into a directory of your choosing 
from GitHub by opening a text terminal and typing:

```
git clone https://github.com/iris-edu/ispaq.git
```

This will produce a copy of this code distribution in the directory you have chosen. When new ispaq versions 
become available, you can update ISPAQ by typing:

```
cd ispaq
git pull origin master
```

## Install the Anaconda Environment

[Anaconda](https://www.continuum.io/why-anaconda) is quickly becoming the *defacto* package manager for 
scientific applications written python or R. [Miniconda](http://conda.pydata.org/miniconda.html) is a trimmed 
down version of Anaconda that contains the bare necessities without loading a large list of data science packages 
up front. With miniconda, you can set up a custom python environment with just the packages you need to run ISPAQ.

Proceed to the [Miniconda](http://conda.pydata.org/miniconda.html) web site to find the installer for your
operating system before proceeding with the instructions below. If you can run ```conda``` from the command 
line, then you know you have it successfully installed.

By setting up a [conda virtual environment](http://conda.pydata.org/docs/using/envs.html), we assure that our 
ISPAQ installation is entirely separate from any other installed software.


### Creating the ispaq environment for macOS or Linux

You will go into the ispaq directory that you created with git, update miniconda, then create an 
environment specially for ispaq. You have to ```activate``` the ISPAQ environment whenever you 
perform installs, updates, or run ISPAQ.

```
cd ispaq
conda update conda
conda create --name ispaq python=2.7
source activate ispaq
conda install -c conda-forge --file ispaq-conda-install.txt
```

_Note:_ if `source activate ispaq` results in the message "No such file or directory" your shell may be csh/tcsh instead of bash. You will need 
to start a bash shell first. Type `bash` in a terminal window and then proceed with `source activate ispaq`.

See what is installed in our (ispaq) environment with:

```
conda list
```

Now install the IRIS R packages for ISPAQ:
```
export MACOSX_DEPLOYMENT_TARGET=10.9    # this line for macOS only
R CMD INSTALL seismicRoll_1.1.3.tar.gz 
R CMD INSTALL IRISSeismic_1.4.9.tar.gz
R CMD INSTALL IRISMustangMetrics_2.2.0.tar.gz 
```

Or alternatively, install the IRIS R packages from CRAN: 
```
./run_ispaq.py -U
```

You should also run `./run_ispaq.py -U` after you update your ISPAQ version to verify that you have both the required minimum versions of anaconda packages and the most recent IRIS R packages.

Note: If you are using macOS and see the error: "'math.h' file not found" when compiling seismicRoll, then it is likely that your command line tools are missing. Try running `xcode-select --install`.

# Using ISPAQ

Every time you use ISPAQ you must ensure that you are running in the proper Anaconda
environment. If you followed the instructions above you only need to type:

```
cd ispaq
source activate ispaq
```

after which your prompt should begin with ```(ispaq) ```. You run ispaq using the ```run_ispaq.py``` 
python script. The example below shows how to get ISPAQ to show the help display.  A leading ```./``` 
is used to indicate that the script is in the current directory.

A list of command-line options is available with the ```--help``` flag:

```
(ispaq) bash-3.2$ ./run_ispaq.py -h
usage: run_ispaq.py [-h] [-P PREFERENCES_FILE] [-M METRICS] [-S STATIONS]
                    [--starttime STARTTIME] [--endtime ENDTIME]
                    [--dataselect_url DATASELECT_URL] [--station_url STATION_URL]
                    [--event_url EVENT_URL] [--resp_dir RESP_DIR]
                    [--csv_dir CSV_DIR] [--psd_dir PSD_DIR] [--pdf_dir PDF_DIR]
                    [--pdf_type PDF_TYPE] [--pdf_interval PDF_INTERVAL]
                    [--plot_include PLOT_INCLUDE] [--sncl_format SNCL_FORMAT]
                    [--sigfigs SIGFIGS]
                    [--log-level {DEBUG,INFO,WARNING,ERROR,CRITICAL}] [-A] [-V]
                    [-U] [-L]

ISPAQ version 2.0.0

single arguments:
  -h, --help                       show this help message and exit
  -V, --version                    show program's version number and exit
  -U, --update-r                   check for and install newer CRAN IRIS Mustang packages 
                                   and/or update required conda packages, and exit
  -L, --list-metrics               list names of available metrics and exit

arguments for running metrics:
  -P PREFERENCES_FILE, --preferences-file PREFERENCES_FILE
                                   path to preference file, default=./preference_files/default.txt
  -M METRICS, --metrics METRICS    metrics alias as defined in preference file or metric name, required
  -S STATIONS, --stations STATIONS
                                   stations alias as defined in preference file or station SNCL, required
  --starttime STARTTIME            starttime in ObsPy UTCDateTime format, required for webservice requests 
                                   and defaults to earliest data file for local data 
                                   examples: YYYY-MM-DD, YYYYMMDD, YYYY-DDD, YYYYDDD[THH:MM:SS]
  --endtime ENDTIME                endtime in ObsPy UTCDateTime format, default=starttime + 1 day; 
                                   if starttime is also not specified then it defaults to the latest data 
                                   file for local data 
                                   examples: YYYY-MM-DD, YYYYMMDD, YYYY-DDD, YYYYDDD[THH:MM:SS]

optional arguments for overriding preference file entries:
  --dataselect_url DATASELECT_URL  FDSN webservice or path to directory with miniSEED files
  --station_url STATION_URL        FDSN webservice or path to stationXML file
  --event_url EVENT_URL            FDSN webservice or path to QuakeML file
  --resp_dir RESP_DIR              path to directory with RESP files
  --csv_dir CSV_DIR                directory to write generated metrics .csv files
  --psd_dir PSD_DIR                directory to write/read existing PSD .csv files
  --pdf_dir PDF_DIR                directory to write generated PDF files
  --pdf_type PDF_TYPE              output format of generated PDFs - text and/or plot
  --pdf_interval PDF_INTERVAL      time span for PDFs - daily and/or aggregated over the entire span
  --plot_include PLOT_INCLUDE      PDF plot graphics options - legend, colorbar, and/or fixed_yaxis_limits, 
                                   or none
  --sncl_format SNCL_FORMAT        format of SNCL aliases and miniSEED file names 
                                   examples:"N.S.L.C","S.N.L.C"
                                   where N=network code, S=station code, L=location code, C=channel code
  --sigfigs SIGFIGS                number of significant figures used for output columns named "value"

other arguments:
  --log-level {DEBUG,INFO,WARNING,ERROR,CRITICAL}
                                   log level printed to console, default="INFO"
  -A, --append                     append to TRANSCRIPT file rather than overwriting
```

For those that prefer to run ISPAQ as a package, you can use the following invocation (using help example):
```
(ispaq) $ python -m ispaq.ispaq --help
````

When calculating metrics, valid arguments for `-M` and `-S` are required and must be provided.
If `-P` is not provided, ISPAQ uses the default preference file located at `ispaq/preference_files/default.txt`.
However, all entries in the preference file can be overridden by command-line options. 
If `--log-level` is not specified, the default log-level is `INFO`.

When `--starttime` is invoked without `--endtime`, metrics are run for a single day. Metrics that are defined 
as day-long metrics (24 hour windows, see metrics documentation at 
[MUSTANG](http://services.iris.edu/mustang/measurements/1)) will be calculated for the time period 
`00:00:00-23:59:59.9999`. An endtime of `YYYY-DD-MM` is interpreted as  `YYYY-DD-MM 00:00:00` so that 
e.g., `--starttime=2016-01-01 --endtime=2016-01-02` will also calculate one day of metrics. When an end time 
greater than one day is requested, metrics will be calculated by cycling through multiple single days to produce 
a measurement for each day. Additionally, and only if using local data files, you can run metrics without specifying 
a start time. In this case, ISPAQ will use a start time corresponding to the earliest file found that matches the 
requested station(s). If end time is also not specified, ISPAQ will use an end time corresponding to the latest file 
found that matches the requested station(s).

### Preference files

The ISPAQ system is designed to be configurable through the use of *preference files*.
These are usually located in the ```preference_files/``` directory. Not surprisingly, the default
preference file is ```preference_files/default.txt```. This file is self describing
with the following comments in the header:

```
# Preferences fall into four categories:
#  * Metrics -- aliases for user defined combinations of metrics (Use with -M)
#  * Station_SNCLs -- aliases for user defined combinations of SNCL patterns (Use with -S)
#                     SNCL patterns are station names formatted as Network.Station.Location.Channel
#                     wildcards * and ? are allowed. SNCL pattern format can be modified 
#                     using the Preferences sncl_format.          
#  * Data_Access -- FDSN web services or local files
#  * Preferences -- additional user preferences
#  * PDF_Preferences -- preferences specific to PDF calculation
#
# This file is in a very simple format.  After each category heading, all lines containing a colon 
# will be interpreted as key:value and made available to ISPAQ.
#
```

**Metric** aliases can be any of one of the predefined options or any user-created `alias: metric` combination, 
where *metric* can be a single metric name or a comma separated list of valid metric names. Aliases cannot be 
combinations of other aliases. 
Example: `myMetrics: num_gaps, sample_mean, cross_talk`.

**Station_SNCL** aliases are user created `alias: Network.Station.Location.Channel` combinations. Station SNCLs 
can be comma separated lists. `*` or `?` wildcards can be used in any of the network, station, location, channel elements. 
Example: `"myStations: IU.ANMO.10.BHZ, IU.*.00.BH?, IU.ANMO.*.?HZ, II.PFO.??.*`. By default, aliases are formatted
as `Network.Station.Location.Channel`. This format pattern can be modified using the `sncl_format`entry discussed below.

_Note:_ When directly specifying a SNCL pattern on the command line, SNCLs containing wildcards should be 
enclosed by quotes to avoid a possible error of unrecognized arguments.

**Data_Access** has four entries describing where to find data, metadata, events, and optionally response files.

* `dataselect_url:` should indicate a *miniSEED* data resource as one of the *FDSN web service aliases* used by ObsPy 
(e.g. `IRIS`), an explicit URL pointing to an FDSN web service domain (e.g. `http://service.iris.edu` ), or a file 
path to a directory containing miniSEED files (_See: "Using Local Data Files", below_).

* `station_url:` should indicate a metadata location as an FDSN web service alias, an explicit URL, or a path 
to a file containing metadata in [StationXML](http://www.fdsn.org/xml/station/) format 
([schema](http://www.fdsn.org/xml/station/fdsn-station-1.0.xsd)). For web services, this should point to the same place as 
`dataselect_url` (e.g. `http://service.iris.edu`). For local metadata, StationXML is read at the channel level and any 
response information is ignored. Local instrument response (if used) is expected to be in RESP file format and specified 
in the `resp_dir` entry (see below). If neither webservices or StationXML is available for metadata, the `station_url` entry 
should be left unspecified (blank). In this case, metrics that do not require metadata will still be calculated. Metrics that 
do require metadata information (cross_talk, polarity_check, orientation_check, transfer_function) will not be calculated 
and will return a log message stating "No available waveforms". 

    If you are starting from a *dataless SEED* metadata file, you can create StationXML from this using the 
[FDSN StationXML-SEED Converter](https://seiscode.iris.washington.edu/projects/stationxml-converter).

* `event_url:` should indicate an *event catalog resource* as an FDSN web service alias (e.g. `USGS`), an 
explicit URL (e.g. `https://earthquake.usgs.gov`), or a path to a file containing event information in 
[QuakeML](https://quake.ethz.ch/quakeml) format 
([schema](https://quake.ethz.ch/quakeml/docs/xml?action=AttachFile&do=get&target=QuakeML-BED-1.2.xsd)). 
Only web service providers that can output text format can be used at this time. This entry will 
only be used by metrics that require event information in order to be calculated (*cross_talk, polarity_check, 
orientation_check*).

* `resp_dir:` should be unspecified or absent if local response files are not used. The default behavior
 is to retrieve response information from [IRIS Evalresp](http://service.iris.edu/irisws/evalresp/1/). 
To use local instrument responses instead of [IRIS Evalresp](http://service.iris.edu/irisws/evalresp/1/),
 this parameter should indicate a path to a directory containing response files 
in [RESP](http://ds.iris.edu/ds/nodes/dmc/data/formats/resp/) format. Local response files are expected to be 
named `RESP.network.station.location.channel` or `RESP.station.network.location.channel`. Filenames with extension `.txt` 
are also acceptable. E.g., `RESP.IU.CASY.00.BH1, RESP.CASY.IU.00.BH1, RESP.IU.CASY.00.BH1.txt.` 

    Response information is only needed when generating PSD derived metrics, PDF plots,
or the transfer_function metric.    

    If you are starting from a dataless SEED, you can create RESP files using [rdseed](http://ds.iris.edu/ds/nodes/dmc/manuals/rdseed/).

**Preferences** has four entries describing ispaq output.

* `csv_dir:` should be followed by a directory path for output of generated metric text files (CSV). 
If the directory does not exist, then it attempts to create that directory.

* `psd_dir:` should be followed by a directory path for writing and reading PSD csv files.
If the directory does not exist, then it defaults to the current working directory. PSD csv files generated
by the 'psd_corrected' metric will be written to a directory structure within 'psd_dir' based on network code and
station code ('psd_dir'/NET/STA)

* `pdf_dir:` should be followed by a directory path for output of PDF csv and png files. These files will be
written to a directory structure within 'pdf_dir' based on network code and station code ('pdf_dir'/NET/STA).

* `sigfigs:` should indicate the number of significant figures used for output columns named "value". Default is 6.

* `sncl_format:` should be the format of sncl aliases and miniSEED file names, must be some combination of
 period separated `N`=network, `S`=station, `L`=location, `C`=channel (e.g., `N.S.L.C, S.N.L.C`).
If no `sncl_format` exists, it defaults to `N.S.L.C`.

**PDF_Preferences** has three entries describing PDF output.

* `pdf_type:` should be followed by either "text","plot", or "text,plot".  
"text" will output PDF information in a csv format file with frequency, power, and hits columns.  
"plot" will output a PDF plot in a png format file.  
"text,plot" will output both.  

* `pdf_interval:` should be followed by either "daily","aggregate", or "daily,aggregate".    
"daily" will calculate separate PDFs for each day between the starttime and endtime.  
"aggregate" will calculate one PDF spanning the starttime to endtime span.  
"daily,aggregate" will calculate both.  

* `plot_include:` should be followed by any of "legend","colorbar","fixed_yaxis_limits".  
"legend" will include the legend for the minimum/maximum/mode PDF statistics curves.  
"colorbar" will include the histogram legend for the PDF.  
"fixed_axis_limits" will plot the PDF with y-axis limits of -25 to -225 dB (if not specified, the y-axis limits are determined by the data).  
"legend,colorbar,fixed_axis_limits" will create a PDF plot with all three features.  

Any of these preference file entries can be overridden by command-line arguments:
`-M "metric name"`, `-S "station SNCL"`, `--dataselect_url`, `--station_url`, `--event_url`, `--resp_dir`, 
`--csv_output_dir`, `--plot_output_dir`, `--sigfigs`, `--sncl_format`,`--pdf_type`, `--pdf_interval`, `--plot_include`

More information about using local files can be found below in the section "Using Local Data Files".

### Output files

ISPAQ will always create a log file named ```ISPAQ_TRANSCRIPT.log``` to record actions taken
and messages generated during processing.

Results of most metrics calculations will be written to .csv files using the following naming scheme:

* `MetricAlias`\_`StationAlias`\_`startdate`\__`businessLogic`.csv

when a single day is specified on the command line or

* `MetricAlias`\_`StationAlias`\_`startdate`\_`enddate`\_`businessLogic`.csv

when multiple days are specified from the command line. End date in this context is inclusive of that day.

_businessLogic_ corresponds to which script is invoked:

| businessLogic | ISPAQ script | metrics |
| ----------|--------------|---------|
| simpleMetrics | simple_metrics.py | most metrics |
| SNRMetrics | SNR_metrics.py | sample_snr   |
| PSDMetrics | PSD_metrics.py | pct_above_nhnm, pct_below_nlnm, dead_channel_{lin,gsn}, psd_corrected, pdf |
| crossTalkMetrics | crossTalk_metrics.py | cross_talk |
| pressureCorrelationMetrics | pressureCorrelation_metrics.py | pressure_effects | 
| crossCorrelationMetrics | crossCorrelation_metrics.py | polarity_check | 
| orientationCheckMetrics | orientationCheck_metrics.py | orientation_check | 
| transferMetrics | transferFunction_metrics.py | transfer_function |

The metric alias psdPdf in the default preference file (or any user defined set with metric 'psd_corrected') will 
generate corrected PSDs in files named:

* `SNCL`\_`startdate`\_PSDcorrected.csv

The metric alias psdPdf in the default preference file (or any user defined set with metric 'pdf') will generate 
PDFs in files named:

* `SNCL`\_`startdate`\_PDF.csv  (for daily PDF text)
* `SNCL`\_`startdate`\_`enddate`\_PDF.csv (for aggregate PDF text)
* `SNCL`\_`startdate`\_PDF.png  (for daily PDF plot)
* `SNCL`\_`startdate`\_`enddate`\_PDF.png  (for aggregate PDF plot)

Note: The metric 'pdf' requires that `SNCL`\_`startdate`\_PSDcorrected.csv files exist in the `psd_dir` specified directory. 
If you run the metric 'pdf' alone and see the warning 'No PSD files found', then try running metric 'psd_corrected'
first to generate the PSD files. You will also see the warning 'No PSD files found' if there is no data available for that day.
These two  metrics can be run simulataneously.

If specifying metrics and station SNCLs from the command line instead of using preference file aliases,
the metric name and station SNCL will be used instead of the MetricAlias and StationAlias in the output
file name. In addition, any instances of command-line wildcards "*" or "?" will be replaced with the letter
"x" in the output file name.

### Command line invocation

Example invocations are found in the ```EXAMPLES``` section and at the end of this `README`. 

You can modify the information printed to the console by modifying the ```--log-level```.
To see detailed progress information use ```--log-level DEBUG```. To hide everything other
than an outright crash use ```--log-level CRITICAL```. If `--log-level` is not invoked, the default is 
to print information at the `INFO` level. The other available levels are `WARNING` and `ERROR`.

The following example demonstrates what you should see. _Note:_ Please ignore the warning message from *matplotlib*. 
It will only occur on first use. 

```
(ispaq) $ run_ispaq.py -M basicStats -S basicStats --starttime 2010-04-20 --log-level INFO
2017-05-26 13:58:12 - INFO - Running ISPAQ version 1.0.0 on Fri May 26 13:58:12 2017
~/miniconda2/envs/ispaq/lib/python2.7/site-packages/matplotlib/font_manager.py:273: UserWarning: Matplotlib is 
building the font cache using fc-list. This may take a moment. 
warnings.warn('Matplotlib is building the font cache using fc-list. This may take a moment.')
2017-05-26 13:58:22 - INFO - Calculating simple metrics for 3 SNCLs on 2010-04-20
2017-05-26 13:58:22 - INFO - 000 Calculating simple metrics for IU.ANMO.00.BH1
2017-05-26 13:58:24 - INFO - 001 Calculating simple metrics for IU.ANMO.00.BH2
2017-05-26 13:58:25 - INFO - 002 Calculating simple metrics for IU.ANMO.00.BHZ
2017-05-26 13:58:26 - INFO - Writing simple metrics to basicStats_basicStats_2010-04-20__simpleMetrics.csv
2017-05-26 13:58:26 - INFO - ALL FINISHED!
```

Additional information about running ISPAQ on the command line can be found by invoking `run_ispaq.py --help`.

### Using Local Data Files

Local data files should be in *miniSEED* format and organized in *network-station-channel-day* files 
with naming convention 
```
Network.Station.Location.Channel.Year.JulianDay.Quality
```
 where `Quality` is optional 
(e.g., `TA.P19K..BHZ.2016.214.M` or `TA.P19K..BHZ.2016.214`). This naming convention can be modified
by using the `sncl_format` entry in the preferences file or the `--sncl_format` option on the command line.
`sncl_format` allows you to specify a different order for `Network.Station.Location.Channel`, although all these 
elements must be present in the file name. 

ISPAQ will search for miniSEED files in the directory specified by `dataselect_url` in the preferences file or 
`--dataselect_url` on the command line. Furthermore, it will recursively follow that directory structure and
look for miniSEED files in directories contained within the `dataselect_url` directory. If more than one file name 
is found that matches the same requested network, station, location, channel, year, and julian day, then the metrics 
will be run on the first file that is found. To request all data files, use preference file *Station_SNCL* alias: 
`*.*.*.*`, or `-S "*.*.*.*"` from the command line". Wildcarding every element is strongly discouraged when using 
FDSN webservices instead of local files.

_Note:_ All data is expected to be in the day file that matches its timestamp; if records do not break on the 
day boundary, data that is not in the correct day file will not be used in the metrics calculation. This can 
lead to cases where, for example, a gap is calculated at the start of a day when the data for that time period 
is in the previous day file.

If your miniSEED files are not already split on day boundaries, one tool that can be used for this task is the 
*dataselect* command-line tool available at [https://github.com/iris-edu/dataselect](https://github.com/iris-edu/dataselect). 
Follow the [releases](https://github.com/iris-edu/dataselect/releases) link in the README to download the latest 
version of the source code. The following example reads the input miniSEED files, splits the records on day
boundaries, and writes to files named `network.station.location.channel.year.julianday.quality`.

Example: `dataselect -Sd -A %n.%s.%l.%c.%Y.%j.%q inputfiles`

### Updating CRAN packages

The command-line argument `-U`, `--update-r` can be used to check CRAN for newer IRISSeismic, seismicRoll, and
IRISMustangMetrics R packages.

```
(ispaq) bash-3.2$ ./run_ispaq.py -U
2019-01-28 15:33:25 - INFO - Running ISPAQ version 2.0.0 on Mon Jan 28 15:33:25 2019
2019-01-28 15:33:27 - INFO - Checking for recommended conda packages...
2019-01-28 15:33:27 - INFO - Required conda packages found
2019-01-28 15:33:27 - INFO - Checking for IRIS R package updates...
--- Please select a CRAN mirror for use in this session ---
Secure CRAN mirrors 

 1: 0-Cloud [https]                   2: Algeria [https]                
 3: Australia (Canberra) [https]      4: Australia (Melbourne 1) [https]
 5: Australia (Melbourne 2) [https]   6: Australia (Perth) [https]             
...

Selection: 1

              package installed   CRAN  upgrade
0         seismicRoll     1.1.3  1.1.3    False
1         IRISSeismic     1.4.9  1.4.9    False
2  IRISMustangMetrics     2.2.0  2.1.3    False

2019-01-28 15:33:39 - INFO - No CRAN packages need updating.

```

If a newer CRAN package does exist, the `-U` option will then automatically download the package from CRAN and
install it. ISPAQ code can be updated using `git pull origin master`. Sometimes it is necessary to update the ISPAQ 
python code in conjunction with the CRAN code.


### List of Metrics

The command-line argument `-L` will list the names of available metrics.

#### Brief Metrics Descriptions and Links to Documentation
 
* **amplifier_saturation**:
The number of times that the 'Amplifier saturation detected' bit in the 'dq_flags' byte is set within a 
miniSEED file. This data quality flag is set by some dataloggers in the fixed section of the miniSEED header. 
The flag was intended to indicate that the preamp is being overdriven, but the exact meaning is 
datalogger-specific. [Documentation](http://service.iris.edu/mustang/metrics/docs/1/desc/amplifier_saturation/)

* **calibration_signal**:
The number of times that the 'Calibration signals present' bit in the 'act_flags' byte is set within a miniSEED 
file. A value of 1 indicates that a calibration signal was being sent to that channel.
[Documentation](http://service.iris.edu/mustang/metrics/docs/1/desc/calibration_signal/)

* **clock_locked**:
The number of times that the 'Clock locked' bit in the 'io_flags' byte is set within a miniSEED file. This 
clock flag is set to 1 by some dataloggers in the fixed section of the miniSEED header to indicate that its 
GPS has locked with enough satellites to obtain a time/position fix.
[Documentation](http://service.iris.edu/mustang/metrics/docs/1/desc/clock_locked/)

* **cross_talk**:
The correlation coefficient of channel pairs from the same sensor. Data windows are defined by seismic events. 
Correlation coefficients near 1 may indicate cross-talk between those channels.
[Documentation](http://service.iris.edu/mustang/metrics/docs/1/desc/cross_talk/)

* **dead_channel_gsn**:
A boolean measurement providing a TRUE or FALSE indication that the median PSD values of channel exhibit an
average 5dB deviation below the NLNM in the 4 to 8s period band as measured using a McNamara PDF noise matrix. 
The TRUE condition is indicated with a numeric representation of '1' and the FALSE condition represented as a '0'.
[Documentation](http://service.iris.edu/mustang/metrics/docs/1/desc/dead_channel_gsn/)
    + channels = [BCDHLM][HX].  

* **dead_channel_lin**:
Dead channel metric - linear fit. This metric is calculated from the mean of all the PSDs generated (typically 47 
for a 24 hour period). Values of the PSD mean curve over the band linLoPeriod:linHiPeriod are fit to a linear curve 
by a least squares linear regression of PSD mean ~ log(period). The dead_channel_lin metric is the standard deviation 
of the fit residuals of this regression. Lower numbers indicate a better fit and a higher likelihood that the mean 
PSD is linear - an indication that the sensor is not returning expected seismic energy.
[Documentation](http://service.iris.edu/mustang/metrics/docs/1/desc/dead_channel_lin/)
    + channels = [BCDHM][HX].

* **digital_filter_charging**:
The number of times that the 'A digital filter may be charging' bit in the 'dq_flags' byte is set within a miniSEED 
file. Data samples acquired while a datalogger is loading filter parameters - such as after a reboot - may contain 
a transient.
[Documentation](http://service.iris.edu/mustang/metrics/docs/1/desc/digital_filter_charging/)

* **digitizer_clipping**:
The number of times that the 'Digitizer clipping detected' bit in the 'dq_flags' byte is set within a miniSEED file. 
This flag indicates that the input voltage has exceeded the maximum range of the ADC.
[Documentation](http://service.iris.edu/mustang/metrics/docs/1/desc/digitizer_clipping/)

* **event_begin**:
The number of times that the 'Beginning of an event, station trigger' bit in the 'act_flags' byte is set within a 
miniSEED file. This metric can be used to quickly identify data days that may have events. It may also indicate 
when trigger parameters need adjusting at a station.
[Documentation](http://service.iris.edu/mustang/metrics/docs/1/desc/event_begin/)

* **event_end**:
The number of times that the 'End of an event, station detrigger' bit in the 'act_flags' byte is set within a 
miniSEED file. This metric can be used to quickly identify data days that may have events. It may also indicate 
when trigger parameters need adjusting at a station.
[Documentation](http://service.iris.edu/mustang/metrics/docs/1/desc/event_end/)

* **event_in_progress**:
The number of times that the 'Event in progress' bit in the 'act_flags' byte is set within a miniSEED file. This 
metric can be used to quickly identify data days that may have events. It may also indicate when trigger 
parameters need adjusting at a station.
[Documentation](http://service.iris.edu/mustang/metrics/docs/1/desc/event_in_progress/)

* **glitches**:
The number of times that the 'Glitches detected' bit in the 'dq_flags' byte is set within a miniSEED file. This 
metric can be used to identify data with large filled values that data users may need to handle in a way that they 
don't affect their research outcomes.
[Documentation](http://service.iris.edu/mustang/metrics/docs/1/desc/glitches/)

* **max_gap**:
Indicates the size of the largest gap encountered within a 24-hour window.
[Documentation](http://service.iris.edu/mustang/metrics/docs/1/desc/max_gap/)

* **max_overlap**:
Indicates the size of the largest overlap in seconds encountered within a 24-hour window.
[Documentation](http://service.iris.edu/mustang/metrics/docs/1/desc/max_overlap/)

* **max_stalta**:
The STALTAMetric function calculates the maximum of STA/LTA of the incoming seismic signal over a 24 hour period. 
In order to reduce computation time of the rolling averages, the averaging window is advanced in 1/2 second 
increments. [Documentation](http://service.iris.edu/mustang/metrics/docs/1/desc/max_stalta/)
    + channels = [BHCDES][HPLX].

* **missing_padded_data**:
The number of times that the 'Missing/padded data present' bit in the 'dq_flags' byte is set within a miniSEED file. 
This metric can be used to identify data with padded values that data users may need to handle in a way that they 
don't affect their research outcomes.
[Documentation](http://service.iris.edu/mustang/metrics/docs/1/desc/missing_padded_data/)

* **num_gaps**:
This metric reports the number of gaps encountered within a 24-hour window.
[Documentation](http://service.iris.edu/mustang/metrics/docs/1/desc/num_gaps/)

* **num_overlaps**:
This metric reports the number of overlaps encountered in a 24-hour window.
[Documentation](http://service.iris.edu/mustang/metrics/docs/1/desc/num_overlaps/)

* **num_spikes**:
This metric uses a rolling Hampel filter, a median absolute deviation (MAD) test, to find outliers in a timeseries. 
The number of discrete spikes is determined after adjacent outliers have been combined into individual spikes.
NOTE: not to be confused with the spikes metric, which is an SOH flag only.
[Documentation](http://service.iris.edu/mustang/metrics/docs/1/desc/num_spikes/)
    + channels = [BH][HX].  

* **orientation_check**:
Determine channel orientations by rotating horizontal channels until the resulting radial component maximizes 
cross-correlation with the Hilbert transform of the vertical component. This metric uses Rayleigh waves from large, 
shallow events.
[Documentation](http://service.iris.edu/mustang/metrics/docs/1/desc/num_spikes/)
    + channels = [BCHLM][HX]. 

* **pct_above_nhnm**:
Percent above New High Noise Model. Percentage of Probability Density Function values that are above the New 
High Noise Model. This value is calculated over the entire time period.
[Documentation](http://service.iris.edu/mustang/metrics/docs/1/desc/pct_above_nhnm/)
    + channels = [BCDHM][HX].  

* **pct_below_nlnm**:
Percent below New Low Noise Model. Percentage of Probability Density Function values that are below the New Low Noise 
Model. This value is calculated over the entire time period.
[Documentation](http://service.iris.edu/mustang/metrics/docs/1/desc/pct_below_nlnm/)
    + channels = [BCDHM][HX].  

* **pdf**:
Probability density function plots and/or text output (controlled by PDF_Preferences in the preference file; or by `--pdf_type`,
`--pdf_interval`, `--plot_include` on the command line). You must have local PSD files written in the format produced by the 
'psd_corrected' metric (below) or run it concurrently with 'psd_corrected'. These files should be in a directory specified by the
'psd_dir' entry in the preference file or by `--psd_dir` on the command line.
[Reference: Ambient Noise Levels in the Continental United States, McNamara and Buland, 2004](https://doi.org/10.1785/012003001)

* **percent_availability**:
The portion of data available for each day is represented as a percentage. 100% data available means full coverage of 
data for the reported start and end time.
[Documentation](http://service.iris.edu/mustang/metrics/docs/1/desc/percent_availability/)

* **polarity_check**:
The signed cross-correlation peak value based on the cross-correlation of two neighboring station channels in 
proximity to a large earthquake signal. A negative peak close to -1.0 can indicate reversed polarity.
[Documentation](http://service.iris.edu/mustang/metrics/docs/1/desc/polarity_check/)
    + channels = [BCFHLM][HX].   

* **pressure_effects**:
The correlation coefficient of a seismic channel and an LDO pressure channel. Large correlation coefficients may 
indicate the presence of atmospheric effects in the seismic data.
[Documentation](http://service.iris.edu/mustang/metrics/docs/1/desc/pressure_effects/)
    + channels = LH., LDO  
  
* **psd_corrected**:
Power spectral density values, corrected for instrument response, in text format (starttime, endtime, 
frequency, power).
[Documentation](http://service.iris.edu/mustang/noise-psd/docs/1/help/)
    + channels = .[HLGNPYXD].

* **sample_max**:
This metric reports largest amplitude value in counts encountered within a 24-hour window.
[Documentation](http://service.iris.edu/mustang/metrics/docs/1/desc/sample_max/)

* **sample_mean**:
This metric reports the average amplitude value in counts over a 24-hour window. This mean is one measure of the 
central tendency of the amplitudes that is calculated from every amplitude value present in the time series. The mean 
value itself may not occur as an amplitude value in the times series.
[Documentation](http://service.iris.edu/mustang/metrics/docs/1/desc/sample_mean/)

* **sample_median**:
This metric reports the middle amplitude value in counts of sorted amplitude values from a 24-hour window. This median 
is one measure of the central tendency of the amplitudes in a time series when values are arranged in sorted order. 
The median value itself always occurs as an amplitude value in the times series.
[Documentation](http://service.iris.edu/mustang/metrics/docs/1/desc/sample_median/)

* **sample_min**:
This metric reports smallest amplitude value in counts encountered within a 24-hour window.
[Documentation](http://service.iris.edu/mustang/metrics/docs/1/desc/sample_min/)

* **sample_rms**:
Displays the RMS variance of trace amplitudes within a 24-hour window.
[Documentation](http://service.iris.edu/mustang/metrics/docs/1/desc/sample_rms/)

* **sample_snr**:
A ratio of the RMS variance calculated from data 30 seconds before and 30 seconds following the predicted 
first-arriving P phase.
[Documentation](http://service.iris.edu/mustang/metrics/docs/1/desc/sample_snr/)
    + channels = .[HLGNPYX].

* **sample_unique**:
This metric reports the number (count) of unique values in data trace over a 24-hour window. 
[Documentation](http://service.iris.edu/mustang/metrics/docs/1/desc/sample_unique/)

* **spikes**:
The number of times that the 'Spikes detected' bit in the 'dq_flags' byte is set within a miniSEED file. This data 
quality flag is set by some dataloggers in the fixed section of the miniSEED header when short-duration spikes have 
been detected in the data. Because spikes have shorter duration than the natural period of most seismic sensors, 
spikes often indicate a problem introduced at or after the datalogger.
[Documentation](http://service.iris.edu/mustang/metrics/docs/1/desc/spikes/)
  
* **suspect_time_tag**:
The number of times that the 'Time tag is questionable' bit in the 'dq_flags' byte is set within a miniSEED file. 
This metric can be used to identify stations with GPS locking problems and data days with potential timing issues.
[Documentation](http://service.iris.edu/mustang/metrics/docs/1/desc/suspect_time_tag/)

* **telemetry_sync_error**:
The number of times that the 'Telemetry synchronization error' bit in the 'dq_flags' byte is set within a miniSEED 
file. This metric can be searched to determine which stations may have telemetry problems or to identify or omit gappy 
data from a data request.
[Documentation](http://service.iris.edu/mustang/metrics/docs/1/desc/telemetry_sync_error/)

* **timing_correction**:
The number of times that the 'Time correction applied' bit in the 'act_flags' byte is set within a miniSEED file. 
This clock quality flag is set by the network operator in the fixed section of the miniSEED header when a timing 
correction stored in field 16 of the miniSEED fixed header has been applied to the data's original time stamp. 
A value of 0 means that no timing correction has been applied.
[Documentation](http://service.iris.edu/mustang/metrics/docs/1/desc/timing_correction/)

* **timing_quality**:
Daily average of the SEED timing quality stored in miniSEED blockette 1001. This value is vendor specific and 
expressed as a percentage of maximum accuracy. Percentage is NULL if not present in the miniSEED.
[Documentation](http://service.iris.edu/mustang/metrics/docs/1/desc/timing_quality/)

* **transfer_function**:
Transfer function metric consisting of the gain ratio, phase difference and magnitude squared of two co-located 
sensors. [Documentation](http://service.iris.edu/mustang/metrics/docs/1/desc/transfer_function/)
    + channels = [BCFHLM][HX].


### Examples Using preference_files/default.txt Preference File

Note: not using `-P` in the command line is the same as specifying `-P preference_files/default.txt`

```
cd ispaq
source activate ispaq
./run_ispaq.py -M basicStats -S basicStats --starttime 2010-100             # starttime specified as julian day
./run_ispaq.py -M stateOfHealth -S ANMO --starttime 2013-01-05              # starttime specified as calendar day
./run_ispaq.py -M gaps -S ANMO --starttime 2011-01-01 --endtime 2011-01-08
./run_ispaq.py -M psdPdf -S psdPdf --starttime 2013-06-01 --endtime 2013-06-08
```

### Example Using Command-line Options to Override Preference File
```
./run_ispaq.py -M sample_mean -S II.KAPI.00.BHZ --starttime 2013-01-05 --dataselect_url ./test_data --station_url ./test_data/II.KAPI_station.xml --csv_dir ./test_out

./run_ispaq.py -M psd_corrected,pdf -S II.KAPI.00.BHZ --starttime 2013-01-05 --endtime 2013-01-08 --dataselect_url ./test_data --station_url ./test_data/II.KAPI_station.xml --psd_dir ./test_out --pdf_dir ./test_out --pdf_type plot --pdf_interval aggregated
```






