__license__ = """
nmlL is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.
 nmlL is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.
 You should have received a copy of the GNU General Public License along
with nmlL; if not, write to the Free Software Foundation, Inc.,
51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA."""

from nml.editors import extract_tables

output_file = "nml_vs.tmLanguage.json"

text1 = """\
{
    "name": "nml",
    "fileTypes": [
        ".nml",
        ".pnml"
    ],
    "patterns": [
        {
            "include": "#comments"
        },
        {
            "include": "#block"
        },
        {
            "include": "#variable"
        },
        {
            "include": "#feature"
        },
        {
            "include": "#callback"
        }
    ],
    "repository": {
        "comments": {
            "patterns": [
                {
                    "name": "comment.line.number-sign.nml",
                    "begin": "//",
                    "end": "$"
                }
            ]
        },
"""

text2 = """\
        "block": {
            "patterns": [
                {
                    "name": "keyword.other.nml",
                    "match": "blocks"
                }
            ]
        },
"""

text3 = """\
        "variable": {
            "patterns": [
                {
                    "name": "support.variable.nml",
                    "match": "variables"
                }
            ]
        },
"""

text4 = """\
        "feature": {
            "patterns": [
                {
                    "name": "support.class.error.nml",
                    "match": "features"
                }
            ]
        },
"""

text5 = """\
        "callback": {
            "patterns": [
                {
                    "name": "constant.numeric.nml",
                    "match": "callbacks"
                }
            ]
        }
"""

text6 = """\
    },
    "scopeName": "source.nml"
}
"""


# Build VS .tmLanguage file
def write_file(fname):
    line = r"(?<![_$[:alnum:]])(?:(?<=\.\.\.)|(?<!\.))("
    lineend = r")(?![_$[:alnum:]])(?:(?=\.\.\.)|(?!\.))"
    with open(fname, "w") as file:
        file.write(text1)
        file.write(text2.replace("blocks", line + "|".join(extract_tables.block_names_table) + lineend))
        file.write(text3.replace("variables", line + "|".join(extract_tables.variables_names_table) + lineend))
        file.write(text4.replace("features", line + "|".join(extract_tables.feature_names_table) + lineend))
        file.write(text5.replace("callbacks", line + "|".join(extract_tables.callback_names_table) + lineend))
        file.write(text6)


def run():
    write_file(output_file)
