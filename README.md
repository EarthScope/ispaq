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

By setting up a [conda virual environment](http://conda.pydata.org/docs/using/envs.html),
we assure that our ISPAQ installation is entirely separate from any other installed software.

### Alternative 1) Creating an environment from a 'spec' file

This method does everything at once.

```
conda list --explicit > ispaq-explicit-spec-file.txt
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
R CMD install IRISMustangMetrics_1.2.4.tar.gz 
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
R CMD install IRISMustangMetrics_1.2.4.tar.gz 
```
