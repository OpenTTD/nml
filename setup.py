#! /usr/bin/env python3

try:
      from cx_Freeze import setup, Executable
except ImportError:
      pass

import sys, os, string, subprocess
from setuptools import setup, Extension, find_packages

version = sys.version_info
if version[0] < 3 or (version[0] == 3 and version[1] < 2):
    sys.exit('ERROR: Sorry, Python 3.2 or later is required for this application.')

# Import our version information
from nml import version_info
version = version_info.get_and_write_version()

setup(name='nml',
      version=version,
      packages=find_packages(),
      description='A tool to compile nml files to grf or nfo files',
      long_description = 'A tool to compile nml files to grf and / or nfo files.' \
                         'NML is a meta-language that aims to be a lot simpler to learn and use than nfo.',
      license='GPL-2.0+',
      classifiers = ['Development Status :: 2 - Pre-Alpha',
                     'Environment :: Console',
                     'Intended Audience :: Developers',
                     'License :: OSI Approved :: GNU General Public License (GPL)',
                     'Operating System :: OS Independent',
                     'Programming Language :: Python :: 3',
                     'Programming Language :: Python :: 3.2',
                     'Programming Language :: Python :: 3.3',
                     'Programming Language :: Python :: 3.4',
                     'Topic :: Software Development :: Compilers',
                     ],
      url='http://dev.openttdcoop.org/projects/nml',
      author='NML Development Team',
      author_email='nml-team@openttdcoop.org',
      entry_points={
          'console_scripts': ['nmlc = nml.main:run']
      },
      ext_modules = [Extension("nml_lz77", ["nml/_lz77.c"], optional=True)],
)
