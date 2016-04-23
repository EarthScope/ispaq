# ISPAQ

*Description goes here.*

## Installing Prerequisites

This python application is best installed by using
[virtualenv](https://python-packaging-user-guide.readthedocs.org/en/latest/projects/#virtualenv)
to set up a virtual environment that isolates package dependencies and then using
[pip](https://python-packaging-user-guide.readthedocs.org/en/latest/projects/#pip)
to install packages.

### virtualenv

*How to install virtualenv.*

### pip

*How to install pip.*

### Setting up a virtual environment

A virtual environment allows users without super user privileges to set
up a local environment where python packages will be installed and referenced

To set up a virtual environment for python 2.7 in your home directory type
the following on OSX:

```virtualenv --python=/usr/bin/python2.7 ~/venvpy27```

To activate the environment type:

```source ~/venvpy27/bin/activate```

You can check that your version of python is now coming from this environment:

```which python```

### Install python prerequisites

All python prerequisites should be installable with ```pip```:

```
pip install numpy
pip install obspy
pip install pandas
pip install rpy2
```

## Installing and Running ispaq from Source

If you have downloaded the [ispaq source](https://github.com/mazamascience/ispaq) you can
enter the top level directory and type:

```python setup.py insall```

In this same directory you can test the installation with:

```ispaq -M metrics_1 -S sncls_1 --starttime=2010-04-20 --verbose```


