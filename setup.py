from setuptools import setup, find_packages

setup(name='ISPAQ',
      version='1.0.0',
      description='',
      author='Mazama Science',
      author_email='info@mazamascience.com',
      url='http://mazamascience.com/',
      license='GNU GENERAL PUBLIC LICENSE',
      packages=find_packages(exclude=['', 'debug']),      
      install_requires=['rpy2', 'future', 'pandas', 'obspy', 'numpy', 'argparse'],
      )
