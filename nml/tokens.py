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

import re
import sys

import ply.lex as lex

from nml import expression, generic

# fmt: off
reserved = {
    "grf":                 "GRF",
    "var":                 "VARIABLE",
    "param":               "PARAMETER",
    "cargotable":          "CARGOTABLE",
    "railtypetable":       "RAILTYPETABLE",
    "roadtypetable":       "ROADTYPETABLE",
    "tramtypetable":       "TRAMTYPETABLE",
    "if":                  "IF",
    "else":                "ELSE",
    "while":               "WHILE",             # reserved
    "item":                "ITEM",              # action 0/3
    "property":            "PROPERTY",
    "graphics":            "GRAPHICS",
    "snowline":            "SNOWLINE",
    "basecost":            "BASECOST",
    "template":            "TEMPLATE",          # sprite template for action1
    "spriteset":           "SPRITESET",         # action 1
    "spritegroup":         "SPRITEGROUP",       # action 2
    "switch":              "SWITCH",            # deterministic varaction2
    "random_switch":       "RANDOMSWITCH",      # random action2
    "produce":             "PRODUCE",           # production action2
    "error":               "ERROR",             # action B
    "disable_item":        "DISABLE_ITEM",
    "replace":             "REPLACESPRITE",     # action A
    "replacenew":          "REPLACENEWSPRITE",  # action 5
    "font_glyph":          "FONTGLYPH",         # action 12
    "deactivate":          "DEACTIVATE",        # action E
    "town_names":          "TOWN_NAMES",        # action F
    "string":              "STRING",
    "return":              "RETURN",
    "livery_override":     "LIVERYOVERRIDE",
    "exit":                "SKIP_ALL",
    "tilelayout":          "TILELAYOUT",
    "spritelayout":        "SPRITELAYOUT",
    "alternative_sprites": "ALT_SPRITES",
    "base_graphics":       "BASE_GRAPHICS",
    "recolour_sprite":     "RECOLOUR_SPRITE",
    "engine_override":     "ENGINE_OVERRIDE",
    "sort":                "SORT_VEHICLES",
    "const":               "CONST"
}
# fmt: on

line_directive1_pat = re.compile(r'\#line\s+(\d+)\s*(\r?\n|"(.*)"\r?\n)')
line_directive2_pat = re.compile(r'\#\s+(\d+)\s+"(.*)"\s*((?:\d+\s*)*)\r?\n')


class NMLLexer:
    """
    @ivar lexer: PLY scanner object.
    @type lexer: L{ply.lex}

    @ivar includes: Stack of included files.
    @type includes: C{List} of L{generic.LinePosition}

    @ivar text: Input text to scan.
    @type text: C{str}
    """

    # Tokens
    tokens = list(reserved.values()) + [
        "ID",
        "PLUS",
        "MINUS",
        "TIMES",
        "DIVIDE",
        "MODULO",
        "AND",
        "OR",
        "XOR",
        "LOGICAL_AND",
        "LOGICAL_OR",
        "LOGICAL_NOT",
        "BINARY_NOT",
        "EQ",
        "LPAREN",
        "RPAREN",
        "SHIFT_LEFT",
        "SHIFT_RIGHT",
        "SHIFTU_RIGHT",
        "COMP_EQ",
        "COMP_NEQ",
        "COMP_LE",
        "COMP_GE",
        "COMP_LT",
        "COMP_GT",
        "COMMA",
        "RANGE",
        "LBRACKET",
        "RBRACKET",
        "LBRACE",
        "RBRACE",
        "TERNARY_OPEN",
        "COLON",
        "SEMICOLON",
        "STRING_LITERAL",
        "NUMBER",
        "FLOAT",
        "UNIT",
    ]

    t_PLUS = r"\+"
    t_MINUS = r"-"
    t_TIMES = r"\*"
    t_MODULO = r"%"
    t_DIVIDE = r"/"
    t_AND = r"&"
    t_OR = r"\|"
    t_XOR = r"\^"
    t_LOGICAL_AND = r"&&"
    t_LOGICAL_OR = r"\|\|"
    t_LOGICAL_NOT = r"!"
    t_BINARY_NOT = r"~"
    t_EQ = r"="
    t_LPAREN = r"\("
    t_RPAREN = r"\)"
    t_SHIFT_LEFT = r"<<"
    t_SHIFT_RIGHT = r">>"
    t_SHIFTU_RIGHT = r">>>"
    t_COMP_EQ = r"=="
    t_COMP_NEQ = r"!="
    t_COMP_LE = r"<="
    t_COMP_GE = r">="
    t_COMP_LT = r"<"
    t_COMP_GT = r">"
    t_COMMA = r","
    t_RANGE = r"\.\."
    t_LBRACKET = r"\["
    t_RBRACKET = r"\]"
    t_LBRACE = r"{"
    t_RBRACE = r"}"
    t_TERNARY_OPEN = r"\?"
    t_COLON = r":"
    t_SEMICOLON = r";"

    def t_FLOAT(self, t):
        r"\d+\.\d+"
        t.value = expression.ConstantFloat(float(t.value), t.lineno)
        return t

    def t_NUMBER(self, t):
        r"(0x[0-9a-fA-F]+)|(\d+)"
        base = 10
        if len(t.value) >= 2 and t.value[0:2] == "0x":
            t.value = t.value[2:]
            base = 16
        t.value = expression.ConstantNumeric(int(t.value, base), t.lineno)
        return t

    def t_UNIT(self, t):
        r"(nfo)|(mph)|(km/h)|(m/s)|(hpI)|(hpM)|(hp)|(kW)|(tons)|(ton)|(kg)|(snow%)"
        return t

    def t_ID(self, t):
        r"[a-zA-Z_][a-zA-Z0-9_]*"
        if t.value in reserved:  # Check for reserved words
            t.type = reserved[t.value]
        else:
            t.type = "ID"
            t.value = expression.Identifier(t.value, t.lineno)
        return t

    def t_STRING_LITERAL(self, t):
        r'"([^"\\]|\\.)*"'
        t.value = expression.StringLiteral(t.value[1:-1], t.lineno)
        return t

    # Ignored characters
    def t_ignore_comment(self, t):
        r"(/\*(\n|.)*?\*/)|(//.*)"
        self.increment_lines(t.value.count("\n"))

    def t_ignore_whitespace(self, t):
        "[ \t\r]+"
        pass

    def t_line_directive1(self, t):
        r'\#line\s+\d+\s*(\r?\n|".*"\r?\n)'
        # See: https://gcc.gnu.org/onlinedocs/cpp/Line-Control.html
        m = line_directive1_pat.match(t.value)
        assert m is not None
        fname = self.lexer.lineno.filename if m.group(3) is None else m.group(3)

        # This type of line directive contains no information about includes, so we have to make some assumptions
        if self.includes and self.includes[-1].filename == fname:
            # Filename equal to the one on top of the stack -> end of an include
            self.includes.pop()
        elif fname != self.lexer.lineno.filename:
            # Not an end of include and not the current file -> start of an include
            self.includes.append(self.lexer.lineno)

        self.set_position(fname, int(m.group(1), 10))
        self.increment_lines(t.value.count("\n") - 1)

    def t_line_directive2(self, t):
        r'\#\s+\d+\s+".*"\s*(\d+\s*)*\r?\n'
        # Format: # lineno filename flags
        # See: https://gcc.gnu.org/onlinedocs/cpp/Preprocessor-Output.html
        m = line_directive2_pat.match(t.value)
        assert m is not None
        line, fname, flags = m.groups()
        line = int(line, 10)
        flags = [int(f, 10) for f in flags.split(" ") if f != ""] if flags is not None else []

        if 1 in flags:
            # File is being included, add current file/line to stack
            self.includes.append(self.lexer.lineno)
        elif 2 in flags:
            # End of include, new file should be equal to the one on top of the stack
            if self.includes and self.includes[-1].filename == fname:
                self.includes.pop()
            else:
                # But of course user input can never be trusted
                generic.print_warning(
                    generic.Warning.GENERIC,
                    "Information about included files is inconsistent, position information for errors may be wrong.",
                )

        self.set_position(fname, line)
        self.increment_lines(t.value.count("\n") - 1)

    def t_newline(self, t):
        r"\n+"
        self.increment_lines(len(t.value))

    def t_error(self, t):
        print(
            (
                "Illegal character '{}' (character code 0x{:02X}) at {}, column {:d}".format(
                    t.value[0], ord(t.value[0]), t.lexer.lineno, self.find_column(t)
                )
            )
        )
        sys.exit(1)

    def build(self, rebuild=False):
        """
        Initial construction of the scanner.
        """
        if rebuild:
            try:
                import os

                os.remove(os.path.normpath(os.path.join(os.path.dirname(__file__), "generated", "lextab.py")))
            except FileNotFoundError:
                # Tried to remove a non existing file
                pass
        self.lexer = lex.lex(module=self, optimize=1, lextab="nml.generated.lextab")

    def setup(self, text, fname):
        """
        Setup scanner for scanning an input file.

        @param text: Input text to scan.
        @type  text: C{str}

        @param fname: Filename associated with the input text (main input file).
        @type  fname: C{str}
        """
        self.includes = []
        self.text = text
        self.set_position(fname, 1)
        self.lexer.input(text)

    def set_position(self, fname, line):
        """
        @note: The lexer.lineno contains a Position object.
        """
        self.lexer.lineno = generic.LinePosition(fname, line, self.includes[:])

    def increment_lines(self, count):
        self.set_position(self.lexer.lineno.filename, self.lexer.lineno.line_start + count)

    def find_column(self, t):
        last_cr = self.text.rfind("\n", 0, t.lexpos)
        if last_cr < 0:
            last_cr = 0
        return t.lexpos - last_cr
