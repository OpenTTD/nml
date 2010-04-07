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
                  | switch'''
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
    if len(t) == 4: t[0] = AssignmentList(t[3], t[1])
    else: t[0] = AssignmentList(t[1])

def p_assignment_string(t):
    'assignment : ID COLON string'
    t[0] = Assignment(t[1], t[3])

def p_assignment_expr(t):
    'assignment : ID COLON expression'
    t[0] = Assignment(t[1], t[3])

def p_param_assignment(t):
    'param_assignment : param EQ expression'
    t[0] = ParameterAssignment(t[1].num, t[3])

def p_string(t):
    '''string : ID
              | ID LPAREN string_param_list RPAREN'''
    if len(t) == 2: t[0] = String(t[1])
    else: t[0] = String(t[1], t[3])

def p_string_param_list(t):
    '''string_param_list : expression
                         | string_param_list COMMA expression'''
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
    'switch : SWITCH LPAREN feature COMMA ID COMMA expression RPAREN LBRACE switch_body RBRACE'
    t[0] = Switch(t[3], t[5], t[7], t[10])

def p_switch_body(t):
    '''switch_body : expression
                   | switch_range switch_body'''
    if len(t) == 2: t[0] = SwitchBody(t[1])
    else: t[0] = t[2].add_range(t[1])

def p_switch_range(t):
    '''switch_range : expression COLON expression
                    | expression RANGE expression COLON expression'''
    if len(t) == 4: t[0] = SwitchRange(t[1], t[1], t[3])
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
