import sys
import ply.lex as lex

reserved = {
    'grf' : 'GRF',
    'var' : 'VARIABLE',
    'param' : 'PARAMETER',
    'cargotable' : 'CARGOTABLE',
    'if' : 'IF',
    'else' : 'ELSE',
    'while' : 'WHILE', # reserved
    'item' : 'ITEM', # action 0/3
    'property' : 'PROPERTY',
    'graphics' : 'GRAPHICS',
    'spriteblock' : 'SPRITEBLOCK', #action 1 + normal action2
    'template' : 'TEMPLATE', #sprite template for action1
    'spriteset' : 'SPRITESET', #action 1
    'spritegroup' : 'SPRITEGROUP', #action 2
    'ground' : 'GROUND',
    'building' : 'BUILDING',
    'childsprite' : 'CHILDSPRITE',
    'switch' : 'SWITCH', #deterministic varaction2
    'random' : 'RANDOM', #random action2
    'error' : 'ERROR', #action B
    'replace' : 'REPLACESPRITE', #action A
    'replacenew' : 'REPLACENEWSPRITE', #action 5
    'font_glyph' : 'FONTGLYPH', #action 12
    'deactivate' : 'DEACTIVATE', #action E
    'town_names' : 'TOWN_NAMES', # action F
    'sounds' : 'SOUNDS', # action 11
    'load_soundfile' : 'LOAD_SOUNDFILE', # action 11
    'import_sound' : 'IMPORT_SOUND',   # action 11
    'string' : 'STRING',
    'return' : 'RETURN',
    'livery_override' : 'LIVERYOVERRIDE',
}

var_ranges = {
    'SELF' : 0x89,
    'PARENT' : 0x8A,
}

tokens = list(reserved.values()) + [
    'ID',
    'PLUS',
    'MINUS',
    'TIMES',
    'DIVIDE',
    'MODULO',
    'AND',
    'OR',
    'XOR',
    'EQ',
    'LPAREN',
    'RPAREN',
    'SHIFT_LEFT',
    'SHIFT_RIGHT',
    'COMP_EQ',
    'COMP_NEQ',
    'COMP_LT',
    'COMP_GT',
    'COMMA',
    'DOT',
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
    'VARRANGE',
    'UNIT',
]

class NMLLexer(object):
    # Tokens
    tokens = tokens

    t_PLUS             = r'\+'
    t_MINUS            = r'-'
    t_TIMES            = r'\*'
    t_MODULO           = r'%'
    t_DIVIDE           = r'/'
    t_AND              = r'&'
    t_OR               = r'\|'
    t_XOR              = r'\^'
    t_EQ               = r'='
    t_LPAREN           = r'\('
    t_RPAREN           = r'\)'
    t_SHIFT_LEFT       = r'<<'
    t_SHIFT_RIGHT      = r'>>'
    t_COMP_EQ          = r'=='
    t_COMP_NEQ         = r'!='
    t_COMP_LT          = r'<'
    t_COMP_GT          = r'>'
    t_COMMA            = r','
    t_DOT              = r'\.'
    t_RANGE            = r'\.\.'
    t_LBRACKET         = r'\['
    t_RBRACKET         = r'\]'
    t_LBRACE           = r'{'
    t_RBRACE           = r'}'
    t_TERNARY_OPEN     = r'\?'
    t_COLON            = r':'
    t_SEMICOLON        = r';'

    def t_ignore_COMMENT(self, t):
        r'(/\*(\n|.)*?\*/)|(//.*)'
        t.lexer.lineno += t.value.count("\n")

    def t_FLOAT(self, t):
        r'\d+\.\d+'
        t.value = float(t.value)
        return t

    def t_NUMBER(self, t):
        r'(0x[0-9a-fA-F]+)|(\d+)'
        base = 10
        if len(t.value) >= 2 and t.value[0:2] == "0x":
            t.value = t.value[2:]
            base = 16
        t.value = int(t.value, base)
        return t

    def t_UNIT(self, t):
        r'(nfo)|(mph)|(km/h)|(m/s)|(hp)|(ton)'
        return t

    def t_ID(self, t):
        r'[a-zA-Z_][a-zA-Z0-9_]*'
        if t.value in var_ranges:
            t.type = 'VARRANGE'
            t.value = var_ranges[t.value]
        else:
            t.type = reserved.get(t.value,'ID')    # Check for reserved words
        return t

    def t_STRING_LITERAL(self, t):
        r'"([^"\\]|\\.)*"'
        t.value = t.value[1:-1]
        return t

    # Ignored characters
    t_ignore = " \t\r"

    def t_newline(self, t):
        r'\n+'
        t.lexer.lineno += t.value.count("\n")

    def t_error(self, t):
        print "Illegal character '%s' at line %d" % (t.value[0], t.lexer.lineno)
        sys.exit(1)


    def build(self, **kwargs):
        self.lexer = lex.lex(module=self, **kwargs)
