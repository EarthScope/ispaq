from setuptools import setup, find_packages
from pip import main as pip

setup(name='ISPAQ',
      version='0.0.4',
      description='',
      author='Mazama Science',
      author_email='info@mazamascience.com',
      url='http://mazamascience.com/',
      license='GNU GENERAL PUBLIC LICENSE',
      packages=find_packages(exclude=['', 'debug']), 
      # Installs in backwards order of the list
      install_requires=['rpy2>=2.7.8', 'future', 'pandas', 'numpy', 'argparse'],
      )


# Because obspy didn't like being installed directly after numpy
pip(['install', 'obspy'])
