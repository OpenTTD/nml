#! /usr/bin/env python

import sys
from distutils.core import setup

if sys.version < '2.5':
    sys.exit('ERROR: Sorry, python 2.5 is required for this application.')

setup(name='nml',
      version='0.1',
      description='A tool to convert nml files to nfo files',
      long_description =
'''A tool to convert nml files to nfo files. NML is a meta-language that aims
to be a lot simpeler to learn and use then nfo.''',
      license='GPLv2',
      classifiers = ['Development Status :: 2 - Pre-Alpha',
                     'Environment :: Console',
                     'Intended Audience :: Developers',
                     'License :: OSI Approved :: GNU General Public License (GPL)',
                     'Operating System :: OS Independent',
                     'Programming Language :: Python',
                     'Topic :: Software Development :: Compilers',
                     ],
      packages=['nml','nml.actions'],
      url='http://dev.openttdcoop.org/projects/nml',
      scripts=['nml2nfo'],
      )
