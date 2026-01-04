#!/usr/bin/env python3

from setuptools import Distribution, Extension, find_packages, setup

import contextlib
import os

try:
    # Update the version by querying git if possible.
    from nml import version_update

    NML_VERSION = version_update.get_and_write_version()
except ImportError:
    # version_update is excluded from released tarballs, so that
    #  only the predetermined version is used when building from one.
    from nml import version_info

    NML_VERSION = version_info.get_nml_version()

default_dist = Distribution()
default_build_py = default_dist.get_command_class('build_py')
default_clean = default_dist.get_command_class('clean')

setup(
    name="nml",
    version=NML_VERSION,
    packages=find_packages(),
    description="An OpenTTD NewGRF compiler for the nml language",
    long_description=(
        "A tool to compile NewGRFs for OpenTTD from nml files"
        "NML is a meta-language that aims to be a lot simpler to"
        " learn and use than nfo used traditionally to write NewGRFs."
    ),
    license="GPL-2.0+",
    classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: GNU General Public License (GPL)",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Programming Language :: Python :: 3.14",
        "Topic :: Software Development :: Compilers",
    ],
    url="https://github.com/OpenTTD/nml",
    author="NML Development Team",
    author_email="info@openttd.org",
    entry_points={"console_scripts": ["nmlc = nml.main:run"]},
    ext_modules=[Extension("nml_lz77", ["nml/_lz77.c"], optional=True)],
    python_requires=">=3.10",
    install_requires=[
        "Pillow>=3.4",
    ],
)
