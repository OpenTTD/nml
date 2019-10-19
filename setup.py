#!/usr/bin/env python3

import os

from setuptools import Extension, find_packages
# Use cx_Freeze on Windows only, to generate an actual executable
if os.name == 'nt':
    from cx_Freeze import setup, Executable
else:
    from setuptools import setup

from nml import version_info
NML_VERSION = version_info.get_and_write_version()

if os.name == 'nt':
    EXE_PARAM = {'executables': [Executable('nmlc')]}
else:
    EXE_PARAM = {'scripts': ['nmlc']}

setup(
    name='nml',
    version=NML_VERSION,
    packages=find_packages(),
    description='An OpenTTD NewGRF compiler for the nml language',
    long_description=('A tool to compile NewGRFs for OpenTTD from nml files'
                      'NML is a meta-language that aims to be a lot simpler to'
                      ' learn and use than nfo used traditionally to write NewGRFs.'),
    license='GPL-2.0+',
    classifiers=['Development Status :: 2 - Pre-Alpha',
                 'Environment :: Console',
                 'Intended Audience :: Developers',
                 'License :: OSI Approved :: GNU General Public License (GPL)',
                 'Operating System :: OS Independent',
                 'Programming Language :: Python :: 3',
                 'Programming Language :: Python :: 3.5',
                 'Programming Language :: Python :: 3.6',
                 'Programming Language :: Python :: 3.7',
                 'Programming Language :: Python :: 3.8',
                 'Topic :: Software Development :: Compilers',
                 ],
    url='https://github.com/OpenTTD/nml',
    author='NML Development Team',
    author_email='nml-team@openttdcoop.org',
    **EXE_PARAM,
    ext_modules=[Extension("nml_lz77", ["nml/_lz77.c"], optional=True)],
    python_requires='>=3.5',
)
