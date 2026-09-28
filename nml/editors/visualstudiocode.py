# SPDX-License-Identifier: GPL-2.0-or-later

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
