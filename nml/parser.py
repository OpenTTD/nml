from ast import *
from nml import generic
from expression import *
from actions import action11

#operator precedence (lower in the list = higher priority)
precedence = (
    ('left','COMMA'),
    ('right','TERNARY_OPEN','COLON'),
    ('left','OR'),
    ('left','XOR'),
    ('left','AND'),
    ('left','COMP_EQ','COMP_NEQ','COMP_LT','COMP_GT'),
    ('left','SHIFT_LEFT','SHIFT_RIGHT'),
    ('left','PLUS','MINUS'),
    ('left','TIMES','DIVIDE','MODULO'),
)

#
# Main script blocks
#
def p_script(t):
    '''script : main_block
              | script main_block'''
    if len(t) == 2: t[0] = [t[1]]
    else: t[0] = t[1] + [t[2]]

def p_main_block(t):
    '''main_block : skipable_block
                  | switch
                  | spriteblock
                  | template_declaration
                  | town_names
                  | sounds
                  | cargotable'''
    t[0] = t[1]

def p_skipable_script(t):
    '''skipable_script : skipable_block
                       | skipable_script skipable_block'''
    if len(t) == 2: t[0] = [t[1]]
    else: t[0] = t[1] + [t[2]]

def p_skipable_block(t):
    '''skipable_block : grf_block
                      | param_assignment
                      | conditional
                      | loop
                      | item
                      | error_block
                      | deactivate
                      | replace
                      | replace_new
                      | font_glyph
                      | property_block
                      | graphics_block
                      | liveryoverride_block'''
    t[0] = t[1]

#
# Expressions
#
def p_const_expression(t):
    'expression : NUMBER'
    t[0] = ConstantNumeric(t[1])

def p_expression_float(t):
    'expression : FLOAT'
    t[0] = ConstantFloat(t[1])

def p_param_expression(t):
    'expression : param'
    t[0] = t[1]

def p_variable_expression(t):
    'expression : variable'
    t[0] = t[1]

def p_expression_id(t):
    'expression : ID'
    t[0] = t[1]

def p_parenthesed_expression(t):
    'expression : LPAREN expression RPAREN'
    t[0] = t[2]

def p_parameter(t):
    'param : PARAMETER LBRACKET expression RBRACKET'
    t[0] = Parameter(t[3])

code_to_op = {
    '+' : Operator.ADD,
    '-' : Operator.SUB,
    '*' : Operator.MUL,
    '/' : Operator.DIV,
    '%' : Operator.MOD,
    '&' : Operator.AND,
    '|' : Operator.OR,
    '^' : Operator.XOR,
    '==' : Operator.CMP_EQ,
    '!=' : Operator.CMP_NEQ,
    '<' : Operator.CMP_LT,
    '>' : Operator.CMP_GT,
    '<<' : Operator.SHIFT_LEFT,
    '>>' : Operator.SHIFT_RIGHT,
}

def p_binop_plus(t):
    '''expression : expression PLUS expression
                  | expression MINUS expression
                  | expression TIMES expression
                  | expression DIVIDE expression
                  | expression MODULO expression
                  | expression AND expression
                  | expression OR expression
                  | expression XOR expression
                  | expression SHIFT_LEFT expression
                  | expression SHIFT_RIGHT expression
                  | expression COMP_EQ expression
                  | expression COMP_NEQ expression
                  | expression COMP_LT expression
                  | expression COMP_GT expression'''
    t[0] = BinOp(code_to_op[t[2]], t[1], t[3]);

def p_unary_minus(t):
    'expression : MINUS expression'
    t[0] = BinOp(code_to_op[t[1]], ConstantNumeric(0), t[2])

def p_variable(t):
    'variable : VARIABLE LBRACKET expression_list RBRACKET'
    t[0] = Variable(*t[3])

def p_function(t):
    'expression : ID LPAREN expression_list RPAREN'
    t[0] = FunctionCall(t[1], t[3])

#
# Commonly used non-terminals that are not expressions
#
def p_array(t):
    'array : LBRACKET expression_list RBRACKET'
    t[0] = t[2]

def p_assignment_list(t):
    '''assignment_list : assignment
                       | assignment_list assignment'''
    if len(t) == 2: t[0] = [t[1]]
    else: t[0] = t[1] + [t[2]]

def p_assignment(t):
    '''assignment : ID COLON string SEMICOLON
                  | ID COLON expression SEMICOLON
                  | ID COLON STRING_LITERAL SEMICOLON'''
    t[0] = Assignment(t[1], t[3])

def p_string(t):
    'string : STRING LPAREN expression_list RPAREN'
    t[0] = String(t[3][0], t[3][1:])

def p_non_empty_expression_list(t):
    '''non_empty_expression_list : expression
                                 | non_empty_expression_list COMMA expression'''
    if len(t) == 2: t[0] = [t[1]]
    else: t[0] = t[1] + [t[3]]

def p_expression_list(t):
    '''expression_list :
                       | non_empty_expression_list'''
    t[0] = [] if len(t) == 1 else t[1]

def p_non_empty_id_list(t):
    '''non_empty_id_list : ID
                         | non_empty_id_list COMMA ID'''
    if len(t) == 2: t[0] = [t[1]]
    else: t[0] = t[1] + [t[3]]

def p_id_list(t):
    '''id_list :
               | non_empty_id_list'''
    t[0] = [] if len(t) == 1 else t[1]

def p_id_array(t):
    'id_array : LBRACKET id_list RBRACKET'
    t[0] = t[2]

#
# Item blocks
#
def p_item(t):
    '''item : ITEM LPAREN expression RPAREN LBRACE skipable_script RBRACE
            | ITEM LPAREN expression COMMA ID RPAREN LBRACE skipable_script RBRACE
            | ITEM LPAREN expression COMMA ID COMMA expression RPAREN LBRACE skipable_script RBRACE'''
    if len(t) == 8: t[0] = Item(t[3], t[6])
    elif len(t) == 10: t[0] = Item(t[3], t[8], t[5])
    else: t[0] = Item(t[3], t[10], t[5], t[7])

def p_property_block(t):
    'property_block : PROPERTY LBRACE property_list RBRACE'
    t[0] = PropertyBlock(t[3])

def p_property_list(t):
    '''property_list : property_assignment
                     | property_list property_assignment'''
    if len(t) == 2: t[0] = [t[1]]
    else: t[0] = t[1] + [t[2]]

def p_property_assignment(t):
    '''property_assignment : ID COLON expression SEMICOLON
                           | ID COLON expression UNIT SEMICOLON
                           | ID COLON string SEMICOLON
                           | ID COLON array SEMICOLON
                           | NUMBER COLON expression
                           | NUMBER COLON expression UNIT SEMICOLON
                           | NUMBER COLON string SEMICOLON
                           | NUMBER COLON array SEMICOLON'''
    unit = None if len(t) == 5 else Unit(t[4])
    t[0] = Property(t[1], t[3], unit)

def p_graphics_block(t):
    'graphics_block : GRAPHICS LBRACE graphics_list RBRACE'
    t[0] = t[3]

def p_liveryoverride_block(t):
    'liveryoverride_block : LIVERYOVERRIDE LPAREN expression RPAREN LBRACE graphics_list RBRACE'
    t[0] = LiveryOverride(t[3], t[6])

def p_graphics_list(t):
    '''graphics_list : ID SEMICOLON
                     | graphics_assignment graphics_list'''
    if isinstance(t[1], basestring): t[0] = GraphicsBlock(t[1])
    else: t[0] = t[2].append_definition(t[1])

def p_graphics_assignment(t):
    'graphics_assignment : ID COLON ID SEMICOLON'
    t[0] = GraphicsDefinition(t[1], t[3])

#
# Program flow control (if/else/while)
#
def p_conditional(t):
    '''conditional : if_else_parts
                   | if_else_parts ELSE LBRACE skipable_script RBRACE'''
    if len(t) > 2:
        parts = t[1] + [Conditional(None, t[4], None)]
    else:
        parts = t[1]

    last = None
    for part in parts:
        if last is None: t[0] = part
        else: last.else_block = part
        last = part

def p_if_else_parts(t):
    '''if_else_parts : IF LPAREN expression RPAREN LBRACE skipable_script RBRACE
                     | if_else_parts ELSE IF LPAREN expression RPAREN LBRACE skipable_script RBRACE'''
    if len(t) == 8: t[0] = [Conditional(t[3], t[6], None)]
    else: t[0] = t[1] + [Conditional(t[5], t[8], None)]

def p_loop(t):
    'loop : WHILE LPAREN expression RPAREN LBRACE skipable_script RBRACE'
    t[0] = Loop(t[3], t[6])

#
# Switch block
#
def p_switch(t):
    'switch : SWITCH LPAREN expression COMMA VARRANGE COMMA ID COMMA expression RPAREN LBRACE switch_body RBRACE'
    t[0] = Switch(t[3], t[5], t[7], t[9], t[12])

def p_switch_body(t):
    'switch_body : switch_ranges switch_value'
    t[0] = SwitchBody(t[1], t[2])

def p_switch_ranges(t):
    '''switch_ranges :
                     | switch_ranges expression COLON switch_value
                     | switch_ranges expression RANGE expression COLON switch_value'''
    if len(t) == 1: t[0] = []
    elif len(t) == 5: t[0] = t[1] + [SwitchRange(t[2], t[2], t[4])]
    else: t[0] = t[1] + [SwitchRange(t[2], t[4], t[6])]

def p_switch_value(t):
    '''switch_value : RETURN expression SEMICOLON
                    | RETURN SEMICOLON
                    | ID SEMICOLON
                    | string SEMICOLON'''
    if len(t) == 4: t[0] = t[2]
    elif t[1] == 'return': t[0] = None
    else: t[0] = t[1]

#
# Real sprites and related stuff
#
def p_real_sprite(t):
    'real_sprite : LBRACKET expression_list RBRACKET'
    t[0] = RealSprite(t[2])

def p_real_sprite_list(t):
    '''real_sprite_list : real_sprite
                        | real_sprite_list real_sprite'''
    if len(t) == 2: t[0] = [t[1]]
    else: t[0] = t[1] + [t[2]]

def p_template_declaration(t):
    'template_declaration : TEMPLATE ID LPAREN id_list RPAREN LBRACE real_sprite_list RBRACE'
    t[0] = TemplateDeclaration(t[2], t[4], t[7])

def p_template_usage(t):
    'template_usage : ID LPAREN expression_list RPAREN'
    t[0] = TemplateUsage(t[1], t[3])

def p_spriteset_contents(t):
    '''spriteset_contents : real_sprite
                          | template_usage
                          | spriteset_contents real_sprite
                          | spriteset_contents template_usage'''
    if len(t) == 2: t[0] = [t[1]]
    else: t[0] = t[1] + [t[2]]

def p_replace(t):
    'replace : REPLACESPRITE LPAREN expression COMMA STRING_LITERAL RPAREN LBRACE spriteset_contents RBRACE'
    t[0] = ReplaceSprite(t[3], t[5], t[8])

def p_replace_new(t):
    '''replace_new : REPLACENEWSPRITE LPAREN expression COMMA STRING_LITERAL RPAREN LBRACE spriteset_contents RBRACE
                   | REPLACENEWSPRITE LPAREN expression COMMA STRING_LITERAL COMMA expression RPAREN LBRACE spriteset_contents RBRACE'''
    if len(t) == 10: t[0] = ReplaceNewSprite(t[3], t[5], ConstantNumeric(0), t[8])
    else: t[0] = ReplaceNewSprite(t[3], t[5], t[7], t[10])

def p_font_glpyh(t):
    'font_glyph : FONTGLYPH LPAREN expression COMMA expression COMMA STRING_LITERAL RPAREN LBRACE spriteset_contents RBRACE'
    t[0] = FontGlyphBlock(t[3], t[5], t[7], t[10])

#
# Sprite blocks and their contents
#
def p_spriteblock(t):
    'spriteblock : SPRITEBLOCK LPAREN expression RPAREN LBRACE spriteset_list RBRACE'
    t[0] = SpriteBlock(t[3], t[6])

def p_spriteset_list(t):
    '''spriteset_list : spriteset
                      | spritegroup
                      | spriteset_list spriteset
                      | spriteset_list spritegroup'''
    if len(t) == 2: t[0] = [t[1]]
    else: t[0] = t[1] + [t[2]]

def p_spriteset(t):
    'spriteset : SPRITESET LPAREN ID COMMA STRING_LITERAL RPAREN LBRACE spriteset_contents RBRACE'
    t[0] = SpriteSet(t[3], t[5], t[8])


def p_spritegroup_normal(t):
    'spritegroup : SPRITEGROUP ID LBRACE spriteview_list RBRACE'
    t[0] = SpriteGroup(t[2], t[4])

def p_spritegroup_layout(t):
    'spritegroup : SPRITEGROUP ID LBRACE layout_sprite_list RBRACE'
    t[0] = LayoutSpriteGroup(t[2], t[4])

def p_spriteview_list(t):
    '''spriteview_list : ID SEMICOLON
                       | spriteview
                       | spriteview_list spriteview'''
    if isinstance(t[1], basestring): t[0] = [SpriteView('default', [t[1]])]
    elif len(t) == 2: t[0] = [t[1]]
    else: t[0] = t[1] + [t[2]]

def p_spriteview(t):
    ''' spriteview : ID COLON id_array SEMICOLON
                   | ID COLON ID SEMICOLON'''
    if isinstance(t[3], list): t[0] = SpriteView(t[1], t[3])
    else: t[0] = SpriteView(t[1], [t[3]])

def p_layout_sprite_list(t):
    '''layout_sprite_list : layout_sprite
                          | layout_sprite_list layout_sprite'''
    if len(t) == 2: t[0] = [t[1]]
    else: t[0] = t[1] + [t[2]]

def p_layout_sprite(t):
    '''layout_sprite : GROUND LBRACE layout_param_list RBRACE
                     | BUILDING LBRACE layout_param_list RBRACE
                     | CHILDSPRITE LBRACE layout_param_list RBRACE'''
    t[0] = LayoutSprite(t[1], t[3])

def p_layout_param_list(t):
    '''layout_param_list : layout_param
                         | layout_param_list layout_param'''
    if len(t) == 2: t[0] = [t[1]]
    else: t[0] = t[1] + [t[2]]

def p_layout_param(t):
    'layout_param : ID COLON expression SEMICOLON'
    t[0] = LayoutParam(t[1], t[3])

#
# Town names
#
def p_town_names(t):
    '''town_names : TOWN_NAMES LPAREN expression RPAREN LBRACE town_names_param_list RBRACE
                  | TOWN_NAMES LBRACE town_names_param_list RBRACE'''
    if len(t) == 8: t[0] = TownNames(t[3], t[6])
    else: t[0] = TownNames(None, t[3])

def p_town_names_param_list(t):
    '''town_names_param_list : town_names_param
                             | town_names_param_list town_names_param'''
    if len(t) == 2: t[0] = [t[1]]
    else: t[0] = t[1] + [t[2]]

def p_town_names_param(t):
    '''town_names_param : ID COLON string SEMICOLON
                        | LBRACE town_names_part_list RBRACE'''
    if len(t) == 5: t[0] = TownNamesParam(t[1], t[3])
    else: t[0] = TownNamesPart(t[2])

def p_town_names_part_list(t):
    '''town_names_part_list : town_names_part
                            | town_names_part_list COMMA town_names_part'''
    if len(t) == 2: t[0] = [t[1]]
    else: t[0] = t[1] + [t[3]]

def p_town_names_part(t):
    '''town_names_part : TOWN_NAMES LPAREN expression COMMA expression RPAREN
                       | ID LPAREN STRING_LITERAL COMMA expression RPAREN'''
    if t[1] == 'town_names': t[0] = TownNamesEntryDefinition(t[3], t[5])
    else: t[0] = TownNamesEntryText(t[1], t[3], t[5])

#
# Sounds
#
def p_sounds(t):
    '''sounds : SOUNDS LBRACE sound_list RBRACE'''
    t[0] = action11.Action11(t[3])

def p_sound_list(t):
    '''sound_list : sound
                  | sound_list sound'''
    if len(t) == 2: t[0] = [t[1]]
    else: t[0] = t[1] + [t[2]]

def p_sound(t):
    '''sound : LOAD_SOUNDFILE LPAREN STRING_LITERAL RPAREN SEMICOLON
             | IMPORT_SOUND LPAREN expression COMMA expression RPAREN SEMICOLON'''
    if len(t) == 6: t[0] = action11.LoadBinaryFile(t[3])
    else: t[0] = action11.ImportSound(t[3], t[5])

#
# Various misc. main script blocks that don't belong anywhere else
#
def p_param_assignment(t):
    'param_assignment : param EQ expression SEMICOLON'
    t[0] = ParameterAssignment(t[1].num, t[3])

def p_error_block(t):
    'error_block : ERROR LPAREN expression_list RPAREN SEMICOLON'
    t[0] = Error(t[3])

def p_cargotable(t):
    'cargotable : CARGOTABLE LBRACE cargotable_list RBRACE'
    t[0] = CargoTable(t[3])

def p_cargotable_list(t):
    '''cargotable_list : ID
                       | cargotable_list COMMA ID'''
    # t is not a real list, so t[-1] does not work.
    if len(t[len(t) - 1]) != 4: raise generic.ScriptError("Each cargo identifier should be exactly 4 bytes long")
    if len(t) == 2: t[0] = [t[1]]
    else: t[0] = t[1] + [t[3]]

def p_deactivate(t):
    'deactivate : DEACTIVATE LPAREN expression_list RPAREN SEMICOLON'
    t[0] = DeactivateBlock(t[3])

def p_grf_block(t):
    'grf_block : GRF LBRACE assignment_list RBRACE'
    t[0] = GRF(t[3])
