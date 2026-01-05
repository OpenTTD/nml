from setuptools import Extension, setup

try:
    # Update the version by querying git if possible.
    from nml import version_update

    NML_VERSION = version_update.get_and_write_version()
except ImportError:
    # version_update is excluded from released tarballs, so that
    #  only the predetermined version is used when building from one.
    from nml import version_info

    NML_VERSION = version_info.get_nml_version()

setup(
    name="nml",
    version=NML_VERSION,
    ext_modules=[Extension("nml_lz77", ["nml/_lz77.c"], optional=True)],
)
