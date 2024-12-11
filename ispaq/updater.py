# -*- coding: utf-8 -*-
"""
Python module containing for updating R packages.
:copyright:
    Mazama Science
:license:
    GNU Lesser General Public License, Version 3
    (http://www.gnu.org/copyleft/lesser.html)
"""

import pandas as pd
import os
import warnings

#from rpy2 import robjects
from rpy2 import rinterface
from rpy2.robjects import pandas2ri
import rpy2.robjects as ro
from rpy2.robjects.packages import importr
from rpy2.robjects.conversion import localconverter



warnings.filterwarnings("ignore", category=RuntimeWarning)
warnings.filterwarnings("ignore", category=UserWarning)

#     R Initialization     -----------------------------------------------------

# Global R options are set here

ro.r('options(download.file.method="curl")')

# Do now show error messages generated inside of the R packages
ro.r('options(show.error.messages=FALSE)')

#     R functions called internally     ----------------------------------------

# NOTE:  These functions behave exactly the same as the R versions and require
# NOTE:  R-compatible objects as arguments.

_R_install_packages = ro.r('utils::install.packages')
#IRIS_packages = ['seismicRoll','IRISSeismic','IRISMustangMetrics']

def install_IRIS_packages(IRIS_packages,logger):
    for package in IRIS_packages:
        try:
            _R_install_packages(package,repos="https://cloud.r-project.org")
            logger.info('Installed %s' % (package))
        except Exception as e:
            logger.error('Unable to install %s: %s' % (package,e))     

def install_IRIS_packages_missing(IRIS_packages,logger):
    # Get version information for locally installed and CRAN available IRIS_packages
    
    r_installed = ro.r("installed.packages()")
    r_installed_names = r_installed.rownames
    pandas2ri.activate()
    installed_names = ro.conversion.rpy2py(r_installed_names).tolist()

    for package in IRIS_packages:
        if package not in installed_names:
            try:
                _R_install_packages(package,repos="https://cloud.r-project.org")
                logger.info('Installed %s' % (package))
            except Exception as e:
                logger.error('Unable to install %s: %s' % (package,e))
    pandas2ri.deactivate()


def get_IRIS_package_versions(IRIS_packages,logger):
    """
    Return a dataframe of version information for IRIS R packages used in ISPAQ.
    """
    
    pandas2ri.activate()    # this facilitates the easy conversion from the r object r_installed into a python object

    # Get version information for locally installed and CRAN available IRIS_packages
    r_installed = ro.r("installed.packages()[c('seismicRoll','IRISSeismic','IRISMustangMetrics'),'Version']")
    installed_versions = r_installed.tolist()
    r_available = ro.r("available.packages(repos='https://cloud.r-project.org')[c('seismicRoll','IRISSeismic','IRISMustangMetrics'),'Version']")
    cran_versions = r_available.tolist()
    
    # Find any 'old' installed packages that available for an upgrade
    r_old = ro.r("old.packages(repos='https://cloud.r-project.org')[,'Package']")
    old = r_old.tolist()

    # Create a needsUpgrade array
    upgrade = [False, False, False]
    for i in range(len(IRIS_packages)):
        if IRIS_packages[i] in old:
            upgrade[i] = True
        
    # Put information in a dataframe
    df = pd.DataFrame({'package': IRIS_packages,
                       'installed': installed_versions,
                       'CRAN': cran_versions,
                       'upgrade': upgrade})
    # Reorder columns from default alphabetic
    df = df[['package','installed','CRAN','upgrade']]
    pandas2ri.deactivate()
    
    return(df)


def update_IRIS_packages(IRIS_packages,logger):
    """
    Automatically upate IRIS R packages used in ISPAQ.    
    """
    df = get_IRIS_package_versions(IRIS_packages,logger)
    packages_to_upgrade = df.package[df.upgrade].tolist()
    
    if len(packages_to_upgrade) == 0:
        logger.info('No CRAN packages need updating.\n')
        
    else:
        for package in packages_to_upgrade:
            try:
                _R_install_packages(package,repos="https://cloud.r-project.org")
                logger.info('Installed %s' % (package))
            except Exception as e:
                logger.error('Unable to install %s: %s' % (package,e))
                


                
    
    
    
# ------------------------------------------------------------------------------


if __name__ == '__main__':
    import doctest
    doctest.testmod(exclude_empty=True)
