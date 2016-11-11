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

from rpy2 import robjects
from rpy2 import rinterface
from rpy2.robjects import pandas2ri

#     R Initialization     -----------------------------------------------------

# Global R options are set here

robjects.r('options(download.file.method="curl")')

# Do now show error messages generated inside of the R packages
###robjects.r('options(show.error.messages=FALSE)')

#     R functions called internally     ----------------------------------------

# NOTE:  These functions behave exactly the same as the R versions and require
# NOTE:  R-compatible objects as arguments.

_R_install_packages = robjects.r('utils::install.packages')


def get_IRIS_package_versions(logger):
    """
    Return a dataframe of version information for IRIS R packages used in ISPAQ.
    """
    IRIS_packages = ['seismicRoll','IRISSeismic','IRISMustangMetrics']
    
    # Get version information for locally installed and CRAN available IRIS_packages
    r_installed = robjects.r("installed.packages()[c('seismicRoll','IRISSeismic','IRISMustangMetrics'),'Version']")
    installed_versions = pandas2ri.ri2py(r_installed).tolist()
    r_available = robjects.r('available.packages()[c("seismicRoll","IRISSeismic","IRISMustangMetrics"),"Version"]')
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


def update_IRIS_packages(logger):
    """
    Automatically upate IRIS R packages used in ISPAQ.    
    """
    df = get_IRIS_package_versions(logger)
    
    packages_to_upgrade = df.package[df.upgrade].tolist()
    
    if len(packages_to_upgrade) == 0:
        logger.info('No packages need updating.\n')
        
    else:
        for package in packages_to_upgrade:
            try:
                # TODO:  automatic package installation needs to be tested
                _R_install_packages(package)
                logger.info('Installed %s' % (package))
            except Exception as e:
                logger.error('Unable to install %s: %s' % (package,e))
                
                
    
    
    
# ------------------------------------------------------------------------------


if __name__ == '__main__':
    import doctest
    doctest.testmod(exclude_empty=True)
