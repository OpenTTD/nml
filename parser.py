from ast import *

precedence = (
    ('left','COMMA'),
    ('right','TERNARY_OPEN','COLON'),
    ('left','OR'),
    ('left','XOR'),
    ('left','AND'),
    ('left','COMP_EQ','COMP_NEQ','COMP_LT','COMP_GT'),
    ('left','PLUS','MINUS'),
    ('left','TIMES','DIVIDE','MODULO'),
)

def p_script(t):
    '''script : main_block
              | script main_block'''
    if len(t) == 2: t[0] = [t[1]]
    else: t[0] = t[1] + [t[2]]

def p_main_block(t):
    '''main_block : skipable_block
                  | switch
                  | spriteblock'''
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
                      | property_block
                      | graphics_block'''
    t[0] = t[1]

def p_deactivate(t):
    'deactivate : DEACTIVATE LPAREN NUMBER RPAREN'
    t[0] = DeactivateBlock(t[3])

def p_grf_block(t):
    'grf_block : GRF LBRACE assignment_list RBRACE'
    t[0] = GRF(t[3])

def p_assignment_list(t):
    '''assignment_list : assignment
                       | assignment_list SEMICOLON assignment'''
    if len(t) == 2: t[0] = [t[1]]
    else: t[0] = t[1] + [t[3]]

def p_assignment(t):
    '''assignment : ID COLON string
                  | ID COLON expression'''
    t[0] = Assignment(t[1], t[3])

def p_param_assignment(t):
    'param_assignment : param EQ expression'
    t[0] = ParameterAssignment(t[1].num, t[3])

def p_string(t):
    '''string : STRING LPAREN ID RPAREN
              | STRING LPAREN ID COMMA param_list RPAREN'''
    if len(t) == 5: t[0] = String(t[3], [])
    else: t[0] = String(t[3], t[5])

def p_param_list(t):
    '''param_list : expression
                  | param_list COMMA expression'''
    if len(t) == 2: t[0] = [t[1]]
    else: t[0] = t[1] + [t[3]]

def p_const_expression(t):
    'expression : NUMBER'
    t[0] = ConstantNumeric(t[1])

def p_param_expression(t):
    'expression : param'
    t[0] = t[1]

def p_variable_expression(t):
    'expression : variable'
    t[0] = t[1]

def p_parenthesed_expression(t):
    'expression : LPAREN expression RPAREN'
    t[0] = t[2]

def p_parameter(t):
    'param : PARAMETER LBRACKET expression RBRACKET'
    t[0] = Parameter(t[3])

def p_conditional(t):
    'conditional : IF LPAREN expression RPAREN LBRACE skipable_script RBRACE else_block'
    t[0] = Conditional(t[3], t[6], t[8])

def p_else_block(t):
    '''else_block :
                  | ELSE LBRACE skipable_script RBRACE
                  | ELSE conditional'''
    if len(t) == 1: t[0] = None
    elif len(t) == 5: t[0] = Conditional(None, t[3], None)
    else: t[0] = t[2]

def p_feature(t):
    'feature : NUMBER'
    t[0] = t[1]

def p_loop(t):
    'loop : WHILE LPAREN expression RPAREN LBRACE skipable_script RBRACE'
    t[0] = Loop(t[3], t[6])

def p_switch(t):
    'switch : SWITCH LPAREN feature COMMA VARSIZE COMMA ID COMMA expression RPAREN LBRACE switch_body RBRACE'
    t[0] = Switch(t[3], t[5], t[7], t[9], t[12])

def p_switch_body(t):
    '''switch_body : RETURN expression
                   | ID
                   | string
                   | switch_range switch_body'''
    if t[1] == 'return': t[0] = SwitchBody(t[2])
    elif len(t) == 3: t[0] = t[2].add_range(t[1])
    else:t[0] = SwitchBody(t[1])

def p_switch_range(t):
    '''switch_range : expression COLON RETURN expression
                    | expression COLON ID
                    | expression COLON string
                    | expression RANGE expression COLON RETURN expression
                    | expression RANGE expression COLON ID
                    | expression RANGE expression COLON string'''
    if len(t) == 5: t[0] = SwitchRange(t[1], t[1], t[4])
    elif len(t) == 4: t[0] = SwitchRange(t[1], t[1], t[3])
    elif len(t) == 7: t[0] = SwitchRange(t[1], t[3], t[6])
    else: t[0] = SwitchRange(t[1], t[3], t[5])

def p_item(t):
    '''item : ITEM LPAREN feature RPAREN LBRACE skipable_script RBRACE
            | ITEM LPAREN feature COMMA expression RPAREN LBRACE skipable_script RBRACE'''
    if len(t) == 8: t[0] = Item(t[3], t[6])
    else: t[0] = Item(t[3], t[8], t[5])

def p_property_block(t):
    'property_block : PROPERTY LBRACE property_list RBRACE'
    t[0] = PropertyBlock(t[3])

def p_property_list(t):
    '''property_list : property_assignment
                     | property_list property_assignment'''
    if len(t) == 2: t[0] = [t[1]]
    else: t[0] = t[1] + [t[2]]

def p_property_assignment(t):
    '''property_assignment : ID COLON expression
                           | ID COLON string
                           | ID COLON ID
                           | NUMBER COLON expression
                           | NUMBER COLON string
                           | NUMBER COLON ID'''
    t[0] = Property(t[1], t[3])

def p_graphics_block(t):
    'graphics_block : GRAPHICS LBRACE graphics_list RBRACE'
    t[0] = GraphicsBlock(t[3])

def p_graphics_list(t):
    '''graphics_list : ID
                     | graphics_assignment graphics_list'''
    if len(t) == 2: t[0] = GraphicsBlock(t[1])
    else: t[0] = t[1].append_definition(t[2])

def p_graphics_assignment(t):
    'graphics_assignment : ID COLON ID'
    t[0] = GraphicsDefinition(t[1], t[3])

def p_spriteblock(t):
    'spriteblock : SPRITEBLOCK LPAREN feature RPAREN LBRACE spriteset_list RBRACE'
    t[0] = SpriteBlock(t[3], t[6])

def p_spriteset_list(t):
    '''spriteset_list : spriteset
                      | spritegroup
                      | spriteset_list spriteset
                      | spriteset_list spritegroup'''
    if len(t) == 2: t[0] = [t[1]]
    else: t[0] = t[1] + [t[2]]

def p_spriteset(t):
    'spriteset : SPRITESET LPAREN ID COMMA STRING_LITERAL RPAREN LBRACE real_sprite_list RBRACE'
    t[0] = SpriteSet(t[3], t[5], t[8])

def p_real_sprite_list(t):
    '''real_sprite_list : real_sprite
                        | real_sprite_list real_sprite'''
    if len(t) == 2: t[0] = [t[1]]
    else: t[0] = t[1] + [t[2]]

def p_spritegroup(t):
    'spritegroup : SPRITEGROUP ID LBRACE spriteview_list RBRACE'
    t[0] = SpriteGroup(t[2], t[4]);

def p_spriteview_list(t):
    '''spriteview_list : ID
                       | spriteview
                       | spriteview_list spriteview'''
    if len(t) == 2: 
        if isinstance(t[1], str): t[0] = [SpriteView('default', [t[1]])]
        else: t[0] = [t[1]]
    else: t[0] = t[1] + [t[2]]

def p_spriteview(t):
    'spriteview : ID COLON id_list'
    t[0] = SpriteView(t[1], t[3])

#comma-seperated list of ID tokens
def p_id_list(t):
    '''id_list : ID
               | id_list COMMA ID'''
    if len(t) == 2: t[0] = [t[1]]
    else: t[0] = t[1] + [t[3]]

#xpos ypos xsize ysize xrel yrel [compression]
#compression (optional) can either be a number, or one of the following:
#NORMAL (=default), TILE_COMPRESSION, STORE_COMPRESSED, NORMAL_NOCROP, TILE_COMPRESSION_NOCROP, STORE_COMPRESSED_NOCROP
def p_real_sprite(t):
    '''real_sprite : LBRACKET sprite_offset sprite_offset sprite_offset sprite_offset sprite_offset sprite_offset RBRACKET
                   | LBRACKET sprite_offset sprite_offset sprite_offset sprite_offset sprite_offset sprite_offset sprite_offset RBRACKET
                   | LBRACKET sprite_offset sprite_offset sprite_offset sprite_offset sprite_offset sprite_offset ID RBRACKET'''
    if len(t) < 10: t[0] = RealSprite(t[2], t[3], t[4], t[5], t[6], t[7])
    else: t[0] = RealSprite(t[2], t[3], t[4], t[5], t[6], t[7], t[8])

def p_sprite_offset(t):
    '''sprite_offset : NUMBER
                    | MINUS NUMBER'''
    if len(t) == 2: t[0] = t[1]
    else: t[0] = -t[2]

#severity, message (one of REQUIRES_TTDPATCH, REQUIRES_DOS_WINDOWS, USED_WITH, INVALID_PARAMETER,
#MUST_LOAD_BEFORE, MUST_LOAD_AFTER, REQUIRES_OPENTTD, or a custom string),
#data (=string to insert in message), number of parameter, number of parameter
def p_error_block(t):
    '''error_block : ERROR LPAREN expression COMMA ID RPAREN
                   | ERROR LPAREN expression COMMA ID COMMA ID RPAREN
                   | ERROR LPAREN expression COMMA ID COMMA ID COMMA expression RPAREN
                   | ERROR LPAREN expression COMMA ID COMMA ID COMMA expression COMMA expression RPAREN'''
    data = None if len(t) < 8 else t[7]
    param1 = None if len(t) < 10 else t[9]
    param2 = None if len(t) < 12 else t[11]
    t[0] = Error(t[3], t[5], data, param1, param2)

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
                  | expression COMP_EQ expression
                  | expression COMP_NEQ expression
                  | expression COMP_LT expression
                  | expression COMP_GT expression'''
    t[0] = BinOp(code_to_op[t[2]], t[1], t[3]);

def p_variable(t):
    '''variable : VARIABLE LBRACKET expression RBRACKET
                | VARIABLE LBRACKET expression COMMA expression RBRACKET'''
    param = None if len(t) == 5 else t[5]
    t[0] = Variable(t[3], param)

def p_function(t):
    '''expression : ID LPAREN RPAREN
                  | ID LPAREN param_list RPAREN'''
    name = t[1]
    args = [] if len(t) == 4 else t[3]
    if name == "min" or name == "max":
        if len(args) != 2: raise ScriptError("wrong number of arguments to " + name)
        op = Operator.MIN if name == "min" else Operator.MAX
        t[0] = BinOp(op, args[0], args[1])
        return
    if len(args) != 0: raise ScriptError("Calls to another action2 can't have arguments")
    t[0] = Variable(ConstantNumeric(0x7E), name)
    

