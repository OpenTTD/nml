#!/usr/bin/env python3

import os

from setuptools import setup, Extension, find_packages
from setuptools.command.build_py import build_py


class NMLBuildPy(build_py):
    def run(self):
        # Create a parser so that nml/generated/{parse,lex}tab.py are generated.
        from nml import parser
        parser.NMLParser(rebuild=True)
        # Then continue with the normal setuptools build.
        super().run()

setup(
    name='nml',
    use_scm_version={
        "write_to": "nml/__version__.py" 
    },
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
    entry_points={
        'console_scripts': ['nmlc = nml.main:run']
    },
    ext_modules=[Extension("nml_lz77", ["nml/_lz77.c"], optional=True)],
    python_requires='>=3.5',
    install_requires=[
        "Pillow>=3.4",
        "ply",
        "setuptools_scm",
    ],
    cmdclass={'build_py': NMLBuildPy}
)
