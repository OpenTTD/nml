#! /usr/bin/env python


import sys, os, string, subprocess
from setuptools import setup


version = sys.version_info
if version[0] < 2 or (version[0] == 2 and version[1] < 5):
    sys.exit('ERROR: Sorry, python 2.5 ... < 3.0 is required for this application.')
if version[0] >= 3:
    sys.exit('WARNING: Sorry, python 3.0 or later is not yet supported. Some parts may not work.')

# For the purpose of the packet information we only use the numeric code

from nml import version_info
version = version_info.get_and_write_version()

setup(name='nml',
      version=version,
      description='A tool to compile nml files to grf or nfo files',
      long_description = 'A tool to compile nml files to grf and / or nfo files.' \
                         'NML is a meta-language that aims to be a lot simpler to learn and use than nfo.',
      license='GPLv2',
      classifiers = ['Development Status :: 2 - Pre-Alpha',
                     'Environment :: Console',
                     'Intended Audience :: Developers',
                     'License :: OSI Approved :: GNU General Public License (GPL)',
                     'Operating System :: OS Independent',
                     'Programming Language :: Python',
                     'Topic :: Software Development :: Compilers',
                     ],
      packages=['nml', 'nml.actions', 'nml.ast', 'nml.expression'],
      url='http://dev.openttdcoop.org/projects/nml',
      author='NML Development Team',
      author_email='nml-team@openttdcoop.org',
      entry_points="""
      [console_scripts]
      nmlc = nml.main:run
      """
      )
