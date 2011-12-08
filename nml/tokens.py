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

import sys, re
import ply.lex as lex
from nml import expression, generic

reserved = {
    'grf' : 'GRF',
    'var' : 'VARIABLE',
    'param' : 'PARAMETER',
    'cargotable' : 'CARGOTABLE',
    'railtypetable' : 'RAILTYPETABLE',
    'if' : 'IF',
    'else' : 'ELSE',
    'while' : 'WHILE', # reserved
    'item' : 'ITEM', # action 0/3
    'property' : 'PROPERTY',
    'graphics' : 'GRAPHICS',
    'snowline' : 'SNOWLINE',
    'basecost' : 'BASECOST', 
    'template' : 'TEMPLATE', #sprite template for action1
    'spriteset' : 'SPRITESET', #action 1
    'spritegroup' : 'SPRITEGROUP', #action 2
    'switch' : 'SWITCH', #deterministic varaction2
    'random_switch' : 'RANDOMSWITCH', #random action2
    'produce' : 'PRODUCE', #production action2
    'error' : 'ERROR', #action B
    'disable_item' : 'DISABLE_ITEM',
    'replace' : 'REPLACESPRITE', #action A
    'replacenew' : 'REPLACENEWSPRITE', #action 5
    'font_glyph' : 'FONTGLYPH', #action 12
    'deactivate' : 'DEACTIVATE', #action E
    'town_names' : 'TOWN_NAMES', # action F
    'string' : 'STRING',
    'return' : 'RETURN',
    'livery_override' : 'LIVERYOVERRIDE',
    'exit' : 'SKIP_ALL',
    'tilelayout' : 'TILELAYOUT',
    'spritelayout' : 'SPRITELAYOUT',
    'alternative_sprites' : 'ALT_SPRITES',
    'base_graphics' : 'BASE_SPRITES',
    'recolour_sprite' : 'RECOLOUR_SPRITE',
    'engine_override' : 'ENGINE_OVERRIDE',
    'sort' : 'SORT_VEHICLES',
}

line_directive1_pat = re.compile(r'\#line\s+(\d+)\s*(\r?\n|"(.*)"\r?\n)')
line_directive2_pat = re.compile(r'\#\s+(\d+)\s+"(.*)"(\s+\d+\s*)?\r?\n')

class NMLLexer(object):

    # Tokens
    tokens = reserved.values() + [
        'ID',
        'PLUS',
        'MINUS',
        'TIMES',
        'DIVIDE',
        'MODULO',
        'AND',
        'OR',
        'XOR',
        'LOGICAL_AND',
        'LOGICAL_OR',
        'LOGICAL_NOT',
        'BINARY_NOT',
        'EQ',
        'LPAREN',
        'RPAREN',
        'SHIFT_LEFT',
        'SHIFT_RIGHT',
        'SHIFTU_RIGHT',
        'COMP_EQ',
        'COMP_NEQ',
        'COMP_LE',
        'COMP_GE',
        'COMP_LT',
        'COMP_GT',
        'COMMA',
        'RANGE',
        'LBRACKET',
        'RBRACKET',
        'LBRACE',
        'RBRACE',
        'TERNARY_OPEN',
        'COLON',
        'SEMICOLON',
        'STRING_LITERAL',
        'NUMBER',
        'FLOAT',
        'UNIT',
    ]

    t_PLUS             = r'\+'
    t_MINUS            = r'-'
    t_TIMES            = r'\*'
    t_MODULO           = r'%'
    t_DIVIDE           = r'/'
    t_AND              = r'&'
    t_OR               = r'\|'
    t_XOR              = r'\^'
    t_LOGICAL_AND      = r'&&'
    t_LOGICAL_OR       = r'\|\|'
    t_LOGICAL_NOT      = r'!'
    t_BINARY_NOT       = r'~'
    t_EQ               = r'='
    t_LPAREN           = r'\('
    t_RPAREN           = r'\)'
    t_SHIFT_LEFT       = r'<<'
    t_SHIFT_RIGHT      = r'>>'
    t_SHIFTU_RIGHT     = r'>>>'
    t_COMP_EQ          = r'=='
    t_COMP_NEQ         = r'!='
    t_COMP_LE          = r'<='
    t_COMP_GE          = r'>='
    t_COMP_LT          = r'<'
    t_COMP_GT          = r'>'
    t_COMMA            = r','
    t_RANGE            = r'\.\.'
    t_LBRACKET         = r'\['
    t_RBRACKET         = r'\]'
    t_LBRACE           = r'{'
    t_RBRACE           = r'}'
    t_TERNARY_OPEN     = r'\?'
    t_COLON            = r':'
    t_SEMICOLON        = r';'

    def t_FLOAT(self, t):
        r'\d+\.\d+'
        t.value = expression.ConstantFloat(float(t.value), t.lineno)
        return t

    def t_NUMBER(self, t):
        r'(0x[0-9a-fA-F]+)|(\d+)'
        base = 10
        if len(t.value) >= 2 and t.value[0:2] == "0x":
            t.value = t.value[2:]
            base = 16
        t.value = expression.ConstantNumeric(int(t.value, base), t.lineno)
        return t

    def t_UNIT(self, t):
        r'(nfo)|(mph)|(km/h)|(m/s)|(hpI)|(hpM)|(hp)|(kW)|(tons)|(ton)|(kg)'
        return t

    def t_ID(self, t):
        r'[a-zA-Z_][a-zA-Z0-9_]*'
        if t.value in reserved: # Check for reserved words
            t.type = reserved[t.value]
        else:
            t.type = 'ID'
            t.value = expression.Identifier(t.value, t.lineno)
        return t

    def t_STRING_LITERAL(self, t):
        r'"([^"\\]|\\.)*"'
        t.value = expression.StringLiteral(t.value[1:-1], t.lineno)
        return t

    # Ignored characters
    def t_ignore_comment(self, t):
        r'(/\*(\n|.)*?\*/)|(//.*)'
        self.increment_lines(t.value.count("\n"))

    def t_ignore_whitespace(self, t):
        "[ \t\r]"
        pass

    def t_line_directive1(self, t):
        r'\#line\s+\d+\s*(\r?\n|".*"\r?\n)'
        m = line_directive1_pat.match(t.value)
        assert m is not None
        fname = self.lexer.lineno.filename if m.group(3) is None else m.group(3)
        self.set_position(fname, int(m.group(1), 10))
        self.increment_lines(t.value.count('\n') - 1)

    def t_line_directive2(self, t):
        r'\#\s+\d+\s+".*"(\s+\d+\s*)?\r?\n'
        m = line_directive2_pat.match(t.value)
        assert m is not None
        self.set_position(m.group(2), int(m.group(1), 10))
        self.increment_lines(t.value.count('\n') - 1)

    def t_newline(self, t):
        r'\n+'
        self.increment_lines(len(t.value))

    def t_error(self, t):
        print "Illegal character '%s' at %s" % (t.value[0], t.lexer.lineno)
        sys.exit(1)



    def build(self, **kwargs):
        self.lexer = lex.lex(module=self, **kwargs)
        self.set_position('input', 1)


    def set_position(self, fname, line):
        """
        @note: The lexer.lineno contains a Position object.
        """
        self.lexer.lineno = generic.LinePosition(fname, line)

    def increment_lines(self, count):
        self.set_position(self.lexer.lineno.filename, self.lexer.lineno.line_start + count)

