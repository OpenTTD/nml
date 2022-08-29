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

import json
from nml.editors import extract_tables

text1 = """\
{
    "name": "newgrfml",
    "scopeName": "source.newgrfml",
    "fileTypes": [
        ".nml",
        ".pnml"
    ],
    "patterns": [
        {
            "include": "#comment"
        },
        {
            "include": "#numeric-literal"
        },
        {
            "include": "#string"
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
        "comment": {
            "patterns": [
                {
                    "name": "comment.line.newgrfml",
                    "begin": "//",
                    "end": "$"
                },
                {
                    "name": "comment.line.newgrfml",
                    "begin": "#",
                    "end": "$"
                },
                {
                    "name": "comment.block.newgrfml",
                    "begin": "/\\\\*",
                    "end": "\\\\*/"
                }
            ]
        },
        "numeric-literal": {
            "patterns": [
                {
                    "name": "constant.numeric.decimal.newgrfml",
                    "match": "\\\\b[0-9]+\\\\b"
                },
                {
                    "name": "constant.numeric.binary.newgrfml",
                    "match": "\\\\b0(b|B)[01]*\\\\b"
                },
                {
                    "name": "constant.numeric.hex.newgrfml",
                    "match": "\\\\b0(x|X)[0-9a-fA-F]*\\\\b"
                }
            ]
        },
        "string": {
            "patterns": [
                {
                    "name": "string.quoted.double.newgrfml",
                    "begin": "\\"",
                    "beginCaptures": {
                        "0": {
                            "name": "punctuation.definition.string.begin.newgrfml"
                        }
                    },
                    "end": "\\"",
                    "endCaptures": {
                        "0": {
                            "name": "punctuation.definition.string.end.newgrfml"
                        }
                    }
                },
                {
                    "name": "string.quoted.single.newgrfml",
                    "begin": "'",
                    "beginCaptures": {
                        "0": {
                            "name": "punctuation.definition.string.begin.newgrfml"
                        }
                    },
                    "end": "'",
                    "endCaptures": {
                        "0": {
                            "name": "punctuation.definition.string.end.newgrfml"
                        }
                    }
                }
            ]
        },
"""

text2 = """\
        "block": {
            "patterns": [
                {
                    "name": "storage.type.primitive.newgrfml",
                    "match": "blocks"
                }
            ]
        },
"""

text3 = """\
        "variable": {
            "patterns": [
                {
                    "name": "variable.other.property.newgrfml",
                    "match": "variables"
                }
            ]
        },
"""

text4 = """\
        "feature": {
            "patterns": [
                {
                    "name": "support.class.newgrfml",
                    "match": "features"
                }
            ]
        },
"""

text5 = """\
        "callback": {
            "patterns": [
                {
                    "name": "constant.numeric.newgrfml",
                    "match": "callbacks"
                }
            ]
        }
"""

text6 = """\
    }
}
"""


def run():
    line = r"(?<![_$[:alnum:]])(?:(?<=\\.\\.\\.)|(?<!\\.))("
    lineend = r")(?![_$[:alnum:]])(?:(?=\\.\\.\\.)|(?!\\.))"
    with open("newgrfml.tmLanguage.json", "w") as file:
        file.write(text1)
        file.write(text2.replace("blocks", line + "|".join(extract_tables.block_names_table) + lineend))
        file.write(text3.replace("variables", line + "|".join(extract_tables.variables_names_table) + lineend))
        file.write(text4.replace("features", line + "|".join(extract_tables.feature_names_table) + lineend))
        file.write(text5.replace("callbacks", line + "|".join(extract_tables.callback_names_table) + lineend))
        file.write(text6)

    # Simple JSON that contains all keywords for suggestion purposes.
    with open("providers.json", "w") as file:
        output = {}
        output["block"] = extract_tables.block_names_table
        output["variables"] = extract_tables.variables_names_table
        output["features"] = extract_tables.feature_names_table
        output["callbacks"] = extract_tables.callback_names_table
        file.write(json.dumps(output, separators=(",", ":")))
