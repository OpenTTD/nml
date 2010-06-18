import sys
from nml import generic, ast, expression, tokens
from actions import action1, action2var, actionD, action11, real_sprite
import ply.yacc as yacc

class NMLParser(object):
    def __init__(self):
        self.lexer = tokens.NMLLexer()
        self.lexer.build()
        self.tokens = self.lexer.tokens
        self.parser = yacc.yacc(debug = False, module = self)

    def parse(self, text):
        return self.parser.parse(text, lexer = self.lexer.lexer)


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

    def p_error(self, t):
        text = "EOF" if t is None else t.value
        raise generic.ScriptError('Syntax error, unexpected token "%s"' % text, t.lineno)


    #
    # Main script blocks
    #
    def p_script(self, t):
        '''script : main_block
                  | script main_block'''
        if len(t) == 2: t[0] = [t[1]]
        else: t[0] = t[1] + [t[2]]

    def p_main_block(self, t):
        '''main_block : skipable_block
                      | switch
                      | spriteblock
                      | template_declaration
                      | town_names
                      | sounds
                      | cargotable
                      | railtype'''
        t[0] = t[1]

    def p_skipable_script(self, t):
        '''skipable_script : skipable_block
                           | skipable_script skipable_block'''
        if len(t) == 2: t[0] = [t[1]]
        else: t[0] = t[1] + [t[2]]

    def p_skipable_block(self, t):
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
    def p_const_expression(self, t):
        'expression : NUMBER'
        t[0] = expression.ConstantNumeric(t[1], t.lineno(1))

    def p_expression_float(self, t):
        'expression : FLOAT'
        t[0] = expression.ConstantFloat(t[1], t.lineno(1))

    def p_param_expression(self, t):
        'expression : param'
        t[0] = t[1]

    def p_variable_expression(self, t):
        'expression : variable'
        t[0] = t[1]

    def p_expression_id(self, t):
        'expression : ID'
        t[0] = t[1]

    def p_parenthesed_expression(self, t):
        'expression : LPAREN expression RPAREN'
        t[0] = t[2]

    def p_parameter(self, t):
        'param : PARAMETER LBRACKET expression RBRACKET'
        t[0] = expression.Parameter(t[3], t.lineno(1))

    code_to_op = {
        '+'  : expression.Operator.ADD,
        '-'  : expression.Operator.SUB,
        '*'  : expression.Operator.MUL,
        '/'  : expression.Operator.DIV,
        '%'  : expression.Operator.MOD,
        '&'  : expression.Operator.AND,
        '|'  : expression.Operator.OR,
        '^'  : expression.Operator.XOR,
        '==' : expression.Operator.CMP_EQ,
        '!=' : expression.Operator.CMP_NEQ,
        '<'  : expression.Operator.CMP_LT,
        '>'  : expression.Operator.CMP_GT,
        '<<' : expression.Operator.SHIFT_LEFT,
        '>>' : expression.Operator.SHIFT_RIGHT,
    }

    def p_binop_plus(self, t):
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
        t[0] = expression.BinOp(self.code_to_op[t[2]], t[1], t[3], t[1].pos);

    def p_ternary_op(self, t):
        'expression : expression TERNARY_OPEN expression COLON expression'
        t[0] = expression.TernaryOp(t[1], t[3], t[5], t[1].pos)

    def p_unary_minus(self, t):
        'expression : MINUS expression'
        t[0] = expression.BinOp(self.code_to_op[t[1]], expression.ConstantNumeric(0), t[2], t.lineno(1))

    def p_variable(self, t):
        'variable : VARIABLE LBRACKET expression_list RBRACKET'
        t[0] = expression.Variable(*t[3])
        t[0].pos = t.lineno(1)

    def p_function(self, t):
        'expression : ID LPAREN expression_list RPAREN'
        t[0] = expression.FunctionCall(t[1], t[3], t[1].pos)

    def p_array(self, t):
        'array : LBRACKET expression_list RBRACKET'
        t[0] = t[2]

    def p_expression_string(self, t):
        'expression : STRING_LITERAL'
        t[0] = t[1]

    #
    # Commonly used non-terminals that are not expressions
    #
    def p_assignment_list(self, t):
        '''assignment_list : assignment
                           | assignment_list assignment'''
        if len(t) == 2: t[0] = [t[1]]
        else: t[0] = t[1] + [t[2]]

    def p_assignment(self, t):
        '''assignment : ID COLON string SEMICOLON
                      | ID COLON expression SEMICOLON'''
        t[0] = ast.Assignment(t[1], t[3])

    def p_string(self, t):
        'string : STRING LPAREN expression_list RPAREN'
        t[0] = expression.String(t[3][0], t[3][1:], t.lineno(1))

    def p_non_empty_expression_list(self, t):
        '''non_empty_expression_list : expression
                                     | non_empty_expression_list COMMA expression'''
        if len(t) == 2: t[0] = [t[1]]
        else: t[0] = t[1] + [t[3]]

    def p_expression_list(self, t):
        '''expression_list :
                           | non_empty_expression_list'''
        t[0] = [] if len(t) == 1 else t[1]

    def p_non_empty_id_list(self, t):
        '''non_empty_id_list : ID
                             | non_empty_id_list COMMA ID'''
        if len(t) == 2: t[0] = [t[1]]
        else: t[0] = t[1] + [t[3]]

    def p_id_list(self, t):
        '''id_list :
                   | non_empty_id_list'''
        t[0] = [] if len(t) == 1 else t[1]

    def p_id_array(self, t):
        'id_array : LBRACKET id_list RBRACKET'
        t[0] = t[2]

    #
    # Item blocks
    #
    def p_item(self, t):
        'item : ITEM LPAREN expression_list RPAREN LBRACE skipable_script RBRACE'
        t[0] = ast.Item(t[3], t[6], t.lineno(1))

    def p_property_block(self, t):
        'property_block : PROPERTY LBRACE property_list RBRACE'
        t[0] = ast.PropertyBlock(t[3])

    def p_property_list(self, t):
        '''property_list : property_assignment
                         | property_list property_assignment'''
        if len(t) == 2: t[0] = [t[1]]
        else: t[0] = t[1] + [t[2]]

    def p_property_assignment(self, t):
        '''property_assignment : ID COLON expression SEMICOLON
                               | ID COLON expression UNIT SEMICOLON
                               | ID COLON string SEMICOLON
                               | ID COLON array SEMICOLON
                               | NUMBER COLON expression
                               | NUMBER COLON expression UNIT SEMICOLON
                               | NUMBER COLON string SEMICOLON
                               | NUMBER COLON array SEMICOLON'''
        val = expression.Array(t[3], t[1].pos) if isinstance(t[3], list) else t[3]
        unit = None if len(t) == 5 else ast.Unit(t[4])
        t[0] = ast.Property(t[1], val, unit, t.lineno(1))

    def p_graphics_block(self, t):
        'graphics_block : GRAPHICS LBRACE graphics_list RBRACE'
        t[0] = t[3]

    def p_liveryoverride_block(self, t):
        'liveryoverride_block : LIVERYOVERRIDE LPAREN expression RPAREN LBRACE graphics_list RBRACE'
        t[0] = ast.LiveryOverride(t[3], t[6])

    def p_graphics_list(self, t):
        '''graphics_list : graphics_assignment_list
                         | graphics_assignment_list ID SEMICOLON
                         | ID SEMICOLON'''
        if len(t) == 2:
            t[0] = ast.GraphicsBlock(t[1], None)
        elif len(t) == 4:
            t[0] = ast.GraphicsBlock(t[1], t[2])
        else:
            t[0] = ast.GraphicsBlock([], t[1])

    def p_graphics_assignment(self, t):
        'graphics_assignment : expression COLON ID SEMICOLON'
        t[0] = ast.GraphicsDefinition(t[1], t[3])

    def p_graphics_assignment_list(self, t):
        '''graphics_assignment_list : graphics_assignment
                                    | graphics_assignment_list graphics_assignment'''
        if len(t) == 2: t[0] = [t[1]]
        else: t[0] = t[1] + [t[2]]

    #
    # Program flow control (if/else/while)
    #
    def p_conditional(self, t):
        '''conditional : if_else_parts
                       | if_else_parts ELSE LBRACE skipable_script RBRACE'''
        if len(t) > 2:
            parts = t[1] + [ast.Conditional(None, t[4], None)]
        else:
            parts = t[1]

        last = None
        for part in parts:
            if last is None: t[0] = part
            else: last.else_block = part
            last = part

    def p_if_else_parts(self, t):
        '''if_else_parts : IF LPAREN expression RPAREN LBRACE skipable_script RBRACE
                         | if_else_parts ELSE IF LPAREN expression RPAREN LBRACE skipable_script RBRACE'''
        if len(t) == 8: t[0] = [ast.Conditional(t[3], t[6], None)]
        else: t[0] = t[1] + [ast.Conditional(t[5], t[8], None)]

    def p_loop(self, t):
        'loop : WHILE LPAREN expression RPAREN LBRACE skipable_script RBRACE'
        t[0] = ast.Loop(t[3], t[6])

    #
    # Switch block
    #
    def p_switch(self, t):
        'switch : SWITCH LPAREN expression COMMA ID COMMA ID COMMA expression RPAREN LBRACE switch_body RBRACE'
        t[0] = ast.Switch(t[3], t[5], t[7], t[9], t[12])

    def p_switch_body(self, t):
        'switch_body : switch_ranges switch_value'
        t[0] = ast.SwitchBody(t[1], t[2])

    def p_switch_ranges(self, t):
        '''switch_ranges :
                         | switch_ranges expression COLON switch_value
                         | switch_ranges expression RANGE expression COLON switch_value'''
        if len(t) == 1: t[0] = []
        elif len(t) == 5: t[0] = t[1] + [action2var.SwitchRange(t[2], t[2], t[4])]
        else: t[0] = t[1] + [action2var.SwitchRange(t[2], t[4], t[6])]

    def p_switch_value(self, t):
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
    def p_real_sprite(self, t):
        'real_sprite : LBRACKET expression_list RBRACKET'
        t[0] = real_sprite.RealSprite(t[2])

    def p_template_declaration(self, t):
        'template_declaration : TEMPLATE ID LPAREN id_list RPAREN LBRACE spriteset_contents RBRACE'
        t[0] = ast.TemplateDeclaration(t[2], t[4], t[7])

    def p_template_usage(self, t):
        'template_usage : ID LPAREN expression_list RPAREN'
        t[0] = real_sprite.TemplateUsage(t[1], t[3])

    def p_spriteset_contents(self, t):
        '''spriteset_contents : real_sprite
                              | template_usage
                              | spriteset_contents real_sprite
                              | spriteset_contents template_usage'''
        if len(t) == 2: t[0] = [t[1]]
        else: t[0] = t[1] + [t[2]]

    def p_replace(self, t):
        'replace : REPLACESPRITE LPAREN expression COMMA STRING_LITERAL RPAREN LBRACE spriteset_contents RBRACE'
        t[0] = ast.ReplaceSprite(t[3], t[5], t[8])

    def p_replace_new(self, t):
        '''replace_new : REPLACENEWSPRITE LPAREN expression COMMA STRING_LITERAL RPAREN LBRACE spriteset_contents RBRACE
                       | REPLACENEWSPRITE LPAREN expression COMMA STRING_LITERAL COMMA expression RPAREN LBRACE spriteset_contents RBRACE'''
        if len(t) == 10: t[0] = ast.ReplaceNewSprite(t[3], t[5], expression.ConstantNumeric(0), t[8])
        else: t[0] = ast.ReplaceNewSprite(t[3], t[5], t[7], t[10])

    def p_font_glpyh(self, t):
        'font_glyph : FONTGLYPH LPAREN expression COMMA expression COMMA STRING_LITERAL RPAREN LBRACE spriteset_contents RBRACE'
        t[0] = ast.FontGlyphBlock(t[3], t[5], t[7], t[10])

    #
    # Sprite blocks and their contents
    #
    def p_spriteblock(self, t):
        'spriteblock : SPRITEBLOCK LPAREN expression RPAREN LBRACE spriteset_list RBRACE'
        t[0] = ast.SpriteBlock(t[3], t[6])

    def p_spriteset_list(self, t):
        '''spriteset_list : spriteset
                          | spritegroup
                          | spriteset_list spriteset
                          | spriteset_list spritegroup'''
        if len(t) == 2: t[0] = [t[1]]
        else: t[0] = t[1] + [t[2]]

    def p_spriteset(self, t):
        'spriteset : SPRITESET LPAREN ID COMMA STRING_LITERAL RPAREN LBRACE spriteset_contents RBRACE'
        t[0] = action1.SpriteSet(t[3], t[5], t[8])


    def p_spritegroup_normal(self, t):
        'spritegroup : SPRITEGROUP ID LBRACE spriteview_list RBRACE'
        t[0] = action1.SpriteGroup(t[2], t[4])

    def p_spritegroup_layout(self, t):
        'spritegroup : SPRITEGROUP ID LBRACE layout_sprite_list RBRACE'
        t[0] = action1.LayoutSpriteGroup(t[2], t[4])

    def p_spriteview_list(self, t):
        '''spriteview_list : ID SEMICOLON
                           | spriteview
                           | spriteview_list spriteview'''
        if isinstance(t[1], expression.Identifier): t[0] = [ast.SpriteView('default', [t[1]])]
        elif len(t) == 2: t[0] = [t[1]]
        else: t[0] = t[1] + [t[2]]

    def p_spriteview(self, t):
        ''' spriteview : ID COLON id_array SEMICOLON
                       | ID COLON ID SEMICOLON'''
        if isinstance(t[3], list): t[0] = ast.SpriteView(t[1], t[3])
        else: t[0] = ast.SpriteView(t[1], [t[3]])

    def p_layout_sprite_list(self, t):
        '''layout_sprite_list : layout_sprite
                              | layout_sprite_list layout_sprite'''
        if len(t) == 2: t[0] = [t[1]]
        else: t[0] = t[1] + [t[2]]

    def p_layout_sprite(self, t):
        '''layout_sprite : GROUND LBRACE layout_param_list RBRACE
                         | BUILDING LBRACE layout_param_list RBRACE
                         | CHILDSPRITE LBRACE layout_param_list RBRACE'''
        t[0] = ast.LayoutSprite(t[1], t[3])

    def p_layout_param_list(self, t):
        '''layout_param_list : layout_param
                             | layout_param_list layout_param'''
        if len(t) == 2: t[0] = [t[1]]
        else: t[0] = t[1] + [t[2]]

    def p_layout_param(self, t):
        'layout_param : ID COLON expression SEMICOLON'
        t[0] = ast.LayoutParam(t[1], t[3])

    #
    # Town names
    #
    def p_town_names(self, t):
        '''town_names : TOWN_NAMES LPAREN expression RPAREN LBRACE town_names_param_list RBRACE
                      | TOWN_NAMES LBRACE town_names_param_list RBRACE'''
        if len(t) == 8: t[0] = ast.TownNames(t[3], t[6], t.lineno(1))
        else: t[0] = ast.TownNames(None, t[3], t.lineno(1))

    def p_town_names_param_list(self, t):
        '''town_names_param_list : town_names_param
                                 | town_names_param_list town_names_param'''
        if len(t) == 2: t[0] = [t[1]]
        else: t[0] = t[1] + [t[2]]

    def p_town_names_param(self, t):
        '''town_names_param : ID COLON string SEMICOLON
                            | LBRACE town_names_part_list RBRACE'''
        if len(t) == 5: t[0] = ast.TownNamesParam(t[1], t[3], t.lineno(1))
        else: t[0] = ast.TownNamesPart(t[2], t.lineno(1))

    def p_town_names_part_list(self, t):
        '''town_names_part_list : town_names_part
                                | town_names_part_list COMMA town_names_part'''
        if len(t) == 2: t[0] = [t[1]]
        else: t[0] = t[1] + [t[3]]

    def p_town_names_part(self, t):
        '''town_names_part : TOWN_NAMES LPAREN expression COMMA expression RPAREN
                           | ID LPAREN STRING_LITERAL COMMA expression RPAREN'''
        if t[1] == 'town_names': t[0] = ast.TownNamesEntryDefinition(t[3], t[5], t.lineno(1))
        else: t[0] = ast.TownNamesEntryText(t[1], t[3], t[5], t.lineno(1))

    #
    # Sounds
    #
    def p_sounds(self, t):
        '''sounds : SOUNDS LBRACE sound_list RBRACE'''
        t[0] = action11.Action11(t[3])

    def p_sound_list(self, t):
        '''sound_list : sound
                      | sound_list sound'''
        if len(t) == 2: t[0] = [t[1]]
        else: t[0] = t[1] + [t[2]]

    def p_sound(self, t):
        '''sound : LOAD_SOUNDFILE LPAREN STRING_LITERAL RPAREN SEMICOLON
                 | IMPORT_SOUND LPAREN expression COMMA expression RPAREN SEMICOLON'''
        if len(t) == 6: t[0] = action11.LoadBinaryFile(t[3])
        else: t[0] = action11.ImportSound(t[3], t[5])

    #
    # Various misc. main script blocks that don't belong anywhere else
    #
    def p_param_assignment(self, t):
        'param_assignment : param EQ expression SEMICOLON'
        t[0] = actionD.ParameterAssignment(t[1].num, t[3])

    def p_error_block(self, t):
        'error_block : ERROR LPAREN expression_list RPAREN SEMICOLON'
        t[0] = ast.Error(t[3])

    def p_cargotable(self, t):
        'cargotable : CARGOTABLE LBRACE cargotable_list RBRACE'
        t[0] = ast.CargoTable(t[3])

    def p_railtypetable(self, t):
        'railtype : RAILTYPETABLE LBRACE cargotable_list RBRACE'
        t[0] = ast.RailtypeTable(t[3])

    def p_cargotable_list(self, t):
        '''cargotable_list : ID
                           | cargotable_list COMMA ID'''
        # t is not a real list, so t[-1] does not work.
        if len(t[len(t) - 1].value) != 4: raise generic.ScriptError("Each cargo/railtype identifier should be exactly 4 bytes long")
        if len(t) == 2: t[0] = [t[1]]
        else: t[0] = t[1] + [t[3]]

    def p_deactivate(self, t):
        'deactivate : DEACTIVATE LPAREN expression_list RPAREN SEMICOLON'
        t[0] = ast.DeactivateBlock(t[3])

    def p_grf_block(self, t):
        'grf_block : GRF LBRACE assignment_list RBRACE'
        t[0] = ast.GRF(t[3])


