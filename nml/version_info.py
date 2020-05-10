__license__ = """
NML is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

NML is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License along
with NML; if not, write to the Free Software Foundation, Inc.,
51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA."""

def get_lib_versions():
    versions = {}
    #PIL
    try:
        import PIL
        versions["PIL"] = PIL.__version__
    except ImportError:
        versions["PIL"] = "Not found!"

    #PLY
    try:
        from ply import lex
        versions["PLY"] = lex.__version__
    except ImportError:
        versions["PLY"] = "Not found!"

    return versions

def get_nml_version():
    # First check if this is a git repository, and use that version if available.
    # (unless this is a released tarball, see below)
    try:
        from nml import version_update
        version = version_update.get_git_version()
        if version:
            return version
    except ImportError:
        # version_update is excluded from release tarballs,
        #  so that the predetermined version is always used.
        pass

    # No repository was found. Return the version which was saved upon build.
    try:
        from nml import __version__
        version = __version__.version
    except ImportError:
        version = 'unknown'
    return version

def get_cli_version():
    # Version string for usage in command line
    result = get_nml_version() + "\n"
    result += "Library versions encountered:\n"
    for lib, lib_ver in get_lib_versions().items():
        result += lib + ": " + lib_ver + "\n"
    return result.strip()
