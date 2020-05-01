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
    try:
        from setuptools_scm import get_version
        return get_version(root="..", relative_to=__file__)
    except LookupError:
        from nml import __version__
        return __version__.version

def get_cli_version():
    #version string for usage in command line
    result = get_nml_version() + "\n"
    result += "Library versions encountered:\n"
    for lib, lib_ver in get_lib_versions().items():
        result += lib + ": " + lib_ver + "\n"
    return result[0:-1] #strip trailing newline

if __name__ == '__main__':
    print(get_nml_version())
