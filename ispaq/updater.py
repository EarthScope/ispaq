# -*- coding: utf-8 -*-
"""
Python module containing for updating R packages.
:copyright:
    Mazama Science
:license:
    GNU Lesser General Public License, Version 3
    (http://www.gnu.org/copyleft/lesser.html)
"""

from __future__ import (absolute_import, division, print_function)

import pandas as pd
import os
import warnings

from rpy2 import robjects
from rpy2 import rinterface
from rpy2.robjects import pandas2ri

os.environ['MACOSX_DEPLOYMENT_TARGET'] = "10.9"
warnings.filterwarnings("ignore", category=RuntimeWarning)
warnings.filterwarnings("ignore", category=UserWarning)

#     R Initialization     -----------------------------------------------------

# Global R options are set here

robjects.r('options(download.file.method="curl")')

# Do now show error messages generated inside of the R packages
robjects.r('options(show.error.messages=FALSE)')

#     R functions called internally     ----------------------------------------

# NOTE:  These functions behave exactly the same as the R versions and require
# NOTE:  R-compatible objects as arguments.

_R_install_packages = robjects.r('utils::install.packages')
#IRIS_packages = ['seismicRoll','IRISSeismic','IRISMustangMetrics']

def install_IRIS_packages(IRIS_packages,logger):
    for package in IRIS_packages:
        try:
            _R_install_packages(package)
            logger.info('Installed %s' % (package))
        except Exception as e:
            logger.error('Unable to install %s: %s' % (package,e))     

def install_IRIS_packages_missing(IRIS_packages,logger):
    # Get version information for locally installed and CRAN available IRIS_packages
    r_installed = robjects.r("installed.packages()")
    installed_names = pandas2ri.ri2py(r_installed.rownames).tolist()
    
    for package in IRIS_packages:
       if package not in installed_names:
           try:
               _R_install_packages(package)
               logger.info('Installed %s' % (package))
           except Exception as e:
               logger.error('Unable to install %s: %s' % (package,e))


def get_IRIS_package_versions(IRIS_packages,logger):
    """
    Return a dataframe of version information for IRIS R packages used in ISPAQ.
    """
    
    # Get version information for locally installed and CRAN available IRIS_packages
    r_installed = robjects.r("installed.packages()[c('seismicRoll','IRISSeismic','IRISMustangMetrics'),'Version']")
    installed_versions = pandas2ri.ri2py(r_installed).tolist()
    r_available = robjects.r("available.packages()[c('seismicRoll','IRISSeismic','IRISMustangMetrics'),'Version']")
    cran_versions = pandas2ri.ri2py(r_available).tolist()
    
    # Find any 'old' installed packages that available for an upgrade
    r_old = robjects.r("old.packages()[,'Package']")
    old = pandas2ri.ri2py(r_old).tolist()
    
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
    
    return(df)


def update_IRIS_packages(IRIS_packages,logger):
    """
    Automatically upate IRIS R packages used in ISPAQ.    
    """
    df = get_IRIS_package_versions(IRIS_packages,logger)
    packages_to_upgrade = df.package[df.upgrade].tolist()
    
    if len(packages_to_upgrade) == 0:
        logger.info('No packages need updating.\n')
        
    else:
        for package in packages_to_upgrade:
            try:
                _R_install_packages(package)
                logger.info('Installed %s' % (package))
            except Exception as e:
                logger.error('Unable to install %s: %s' % (package,e))
                


                
    
    
    
# ------------------------------------------------------------------------------


if __name__ == '__main__':
    import doctest
    doctest.testmod(exclude_empty=True)
