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

import ply.yacc as yacc

from nml import expression, generic, nmlop, tokens, unit
from nml.actions import actionD, real_sprite
from nml.ast import (
    alt_sprites,
    assignment,
    base_graphics,
    basecost,
    cargotable,
    conditional,
    constant,
    deactivate,
    disable_item,
    error,
    font,
    general,
    grf,
    item,
    loop,
    override,
    produce,
    replace,
    skipall,
    snowline,
    sort_vehicles,
    spriteblock,
    switch,
    tilelayout,
    townnames,
    tracktypetable,
)


class NMLParser:
    """
    @ivar lexer: Scanner providing tokens.
    @type lexer: L{NMLLexer}

    @ivar tokens: Tokens of the scanner (used by PLY).
    @type tokens: C{List} of C{str}

    @ivar parser: PLY parser.
    @type parser: L{ply.yacc}
    """

    def __init__(self, rebuild=False, debug=False):
        if debug:
            try:
                import os

                os.remove(os.path.normpath(os.path.join(os.path.dirname(__file__), "generated", "parsetab.py")))
            except FileNotFoundError:
                # Tried to remove a non existing file
                pass
        self.lexer = tokens.NMLLexer()
        self.lexer.build(rebuild or debug)
        self.tokens = self.lexer.tokens
        self.parser = yacc.yacc(
            module=self,
            debug=debug,
            optimize=not (rebuild or debug),
            write_tables=not debug,
            tabmodule="nml.generated.parsetab",
        )

    def parse(self, text, input_filename):
        self.lexer.setup(text, input_filename)
        return self.parser.parse(None, lexer=self.lexer.lexer)

    # operator precedence (lower in the list = higher priority)
    precedence = (
        ("left", "COMMA"),
        ("right", "TERNARY_OPEN", "COLON"),
        ("left", "LOGICAL_OR"),
        ("left", "LOGICAL_AND"),
        ("left", "OR"),
        ("left", "XOR"),
        ("left", "AND"),
        ("left", "COMP_EQ", "COMP_NEQ", "COMP_LE", "COMP_GE", "COMP_LT", "COMP_GT"),
        ("left", "SHIFT_LEFT", "SHIFT_RIGHT", "SHIFTU_RIGHT"),
        ("left", "PLUS", "MINUS"),
        ("left", "TIMES", "DIVIDE", "MODULO"),
        ("left", "LOGICAL_NOT", "BINARY_NOT"),
    )

    def p_error(self, t):
        if t is None:
            raise generic.ScriptError("Syntax error, unexpected end-of-file")
        else:
            raise generic.ScriptError('Syntax error, unexpected token "{}"'.format(t.value), t.lineno)

    #
    # Main script blocks
    #
    def p_main_script(self, t):
        "main_script : script"
        t[0] = general.MainScript(t[1])

    def p_script(self, t):
        """script :
        | script main_block"""
        if len(t) == 1:
            t[0] = []
        else:
            t[0] = t[1] + [t[2]]

    def p_main_block(self, t):
        """main_block : switch
        | random_switch
        | produce
        | spriteset
        | spritegroup
        | spritelayout
        | template_declaration
        | tilelayout
        | town_names
        | cargotable
        | railtype
        | roadtype
        | tramtype
        | grf_block
        | param_assignment
        | skip_all
        | conditional
        | loop
        | item
        | property_block
        | graphics_block
        | liveryoverride_block
        | error_block
        | disable_item
        | deactivate
        | replace
        | replace_new
        | base_graphics
        | font_glyph
        | alt_sprites
        | snowline
        | engine_override
        | sort_vehicles
        | basecost
        | constant"""
        t[0] = t[1]

    #
    # Expressions
    #
    def p_expression(self, t):
        """expression : NUMBER
        | FLOAT
        | param
        | variable
        | ID
        | STRING_LITERAL
        | string"""
        t[0] = t[1]

    def p_parenthesed_expression(self, t):
        "expression : LPAREN expression RPAREN"
        t[0] = t[2]

    def p_parameter(self, t):
        "param : PARAMETER LBRACKET expression RBRACKET"
        t[0] = expression.Parameter(t[3], t.lineno(1), True)

    def p_parameter_other_grf(self, t):
        "param : PARAMETER LBRACKET expression COMMA expression RBRACKET"
        t[0] = expression.OtherGRFParameter(t[3], t[5], t.lineno(1))

    code_to_op = {
        "+": nmlop.ADD,
        "-": nmlop.SUB,
        "*": nmlop.MUL,
        "/": nmlop.DIV,
        "%": nmlop.MOD,
        "&": nmlop.AND,
        "|": nmlop.OR,
        "^": nmlop.XOR,
        "&&": nmlop.AND,
        "||": nmlop.OR,
        "==": nmlop.CMP_EQ,
        "!=": nmlop.CMP_NEQ,
        "<=": nmlop.CMP_LE,
        ">=": nmlop.CMP_GE,
        "<": nmlop.CMP_LT,
        ">": nmlop.CMP_GT,
        "<<": nmlop.SHIFT_LEFT,
        ">>": nmlop.SHIFT_RIGHT,
        ">>>": nmlop.SHIFTU_RIGHT,
    }

    def p_binop(self, t):
        """expression : expression PLUS expression
        | expression MINUS expression
        | expression TIMES expression
        | expression DIVIDE expression
        | expression MODULO expression
        | expression AND expression
        | expression OR expression
        | expression XOR expression
        | expression SHIFT_LEFT expression
        | expression SHIFT_RIGHT expression
        | expression SHIFTU_RIGHT expression
        | expression COMP_EQ expression
        | expression COMP_NEQ expression
        | expression COMP_LE expression
        | expression COMP_GE expression
        | expression COMP_LT expression
        | expression COMP_GT expression"""
        t[0] = expression.BinOp(self.code_to_op[t[2]], t[1], t[3], t[1].pos)

    def p_binop_logical(self, t):
        """expression : expression LOGICAL_AND expression
        | expression LOGICAL_OR expression"""
        t[0] = expression.BinOp(self.code_to_op[t[2]], expression.Boolean(t[1]), expression.Boolean(t[3]), t[1].pos)

    def p_logical_not(self, t):
        "expression : LOGICAL_NOT expression"
        t[0] = expression.Not(expression.Boolean(t[2]), t.lineno(1))

    def p_binary_not(self, t):
        "expression : BINARY_NOT expression"
        t[0] = expression.BinNot(t[2], t.lineno(1))

    def p_ternary_op(self, t):
        "expression : expression TERNARY_OPEN expression COLON expression"
        t[0] = expression.TernaryOp(t[1], t[3], t[5], t[1].pos)

    def p_unary_minus(self, t):
        "expression : MINUS expression"
        t[0] = nmlop.SUB(0, t[2], t.lineno(1))

    def p_variable(self, t):
        "variable : VARIABLE LBRACKET expression_list RBRACKET"
        t[0] = expression.Variable(*t[3])
        t[0].pos = t.lineno(1)

    def p_function(self, t):
        "expression : ID LPAREN expression_list RPAREN"
        t[0] = expression.FunctionCall(t[1], t[3], t[1].pos)

    def p_array(self, t):
        "expression : LBRACKET expression_list RBRACKET"
        t[0] = expression.Array(t[2], t.lineno(1))

    #
    # Commonly used non-terminals that are not expressions
    #
    def p_assignment_list(self, t):
        """assignment_list : assignment
        | param_desc
        | assignment_list assignment
        | assignment_list param_desc"""
        if len(t) == 2:
            t[0] = [t[1]]
        else:
            t[0] = t[1] + [t[2]]

    def p_assignment(self, t):
        "assignment : ID COLON expression SEMICOLON"
        t[0] = assignment.Assignment(t[1], t[3], t[1].pos)

    def p_param_desc(self, t):
        """param_desc : PARAMETER expression LBRACE setting_list RBRACE
        | PARAMETER LBRACE setting_list RBRACE"""
        if len(t) == 5:
            t[0] = grf.ParameterDescription(t[3])
        else:
            t[0] = grf.ParameterDescription(t[4], t[2])

    def p_setting_list(self, t):
        """setting_list : setting
        | setting_list setting"""
        if len(t) == 2:
            t[0] = [t[1]]
        else:
            t[0] = t[1] + [t[2]]

    def p_setting(self, t):
        "setting : ID LBRACE setting_value_list RBRACE"
        t[0] = grf.ParameterSetting(t[1], t[3])

    def p_setting_value_list(self, t):
        """setting_value_list : setting_value
        | setting_value_list setting_value"""
        if len(t) == 2:
            t[0] = [t[1]]
        else:
            t[0] = t[1] + [t[2]]

    def p_setting_value(self, t):
        "setting_value : assignment"
        t[0] = t[1]

    def p_names_setting_value(self, t):
        "setting_value : ID COLON LBRACE name_string_list RBRACE SEMICOLON"
        t[0] = assignment.Assignment(t[1], t[4], t[1].pos)

    def p_name_string_list(self, t):
        """name_string_list : name_string_item
        | name_string_list name_string_item"""
        if len(t) == 2:
            t[0] = expression.Array([t[1]], t[1].pos)
        else:
            t[0] = expression.Array(t[1].values + [t[2]], t[1].pos)

    def p_name_string_item(self, t):
        "name_string_item : expression COLON string SEMICOLON"
        t[0] = assignment.Assignment(t[1], t[3], t[1].pos)

    def p_string(self, t):
        "string : STRING LPAREN expression_list RPAREN"
        t[0] = expression.String(t[3], t.lineno(1))

    def p_non_empty_expression_list(self, t):
        """non_empty_expression_list : expression
        | non_empty_expression_list COMMA expression"""
        if len(t) == 2:
            t[0] = [t[1]]
        else:
            t[0] = t[1] + [t[3]]

    def p_expression_list(self, t):
        """expression_list :
        | non_empty_expression_list
        | non_empty_expression_list COMMA"""
        t[0] = [] if len(t) == 1 else t[1]

    def p_non_empty_id_list(self, t):
        """non_empty_id_list : ID
        | non_empty_id_list COMMA ID"""
        if len(t) == 2:
            t[0] = [t[1]]
        else:
            t[0] = t[1] + [t[3]]

    def p_id_list(self, t):
        """id_list :
        | non_empty_id_list
        | non_empty_id_list COMMA"""
        t[0] = [] if len(t) == 1 else t[1]

    def p_generic_assignment(self, t):
        "generic_assignment : expression COLON expression SEMICOLON"
        t[0] = assignment.Assignment(t[1], t[3], t.lineno(1))

    def p_generic_assignment_list(self, t):
        """generic_assignment_list :
        | generic_assignment_list generic_assignment"""
        t[0] = [] if len(t) == 1 else t[1] + [t[2]]

    def p_snowline_assignment(self, t):
        """snowline_assignment : expression COLON expression SEMICOLON
        | expression COLON expression UNIT SEMICOLON"""
        unit_value = None if len(t) == 5 else unit.get_unit(t[4])
        t[0] = assignment.UnitAssignment(t[1], t[3], unit_value, t.lineno(1))

    def p_snowline_assignment_list(self, t):
        """snowline_assignment_list :
        | snowline_assignment_list snowline_assignment"""
        t[0] = [] if len(t) == 1 else t[1] + [t[2]]

    #
    # Item blocks
    #
    def p_item(self, t):
        "item : ITEM LPAREN expression_list RPAREN LBRACE script RBRACE"
        t[0] = item.Item(t[3], t[6], t.lineno(1))

    def p_property_block(self, t):
        "property_block : PROPERTY LBRACE property_list RBRACE"
        t[0] = item.PropertyBlock(t[3], t.lineno(1))

    def p_property_list(self, t):
        """property_list : property_assignment
        | property_list property_assignment"""
        if len(t) == 2:
            t[0] = [t[1]]
        else:
            t[0] = t[1] + [t[2]]

    def p_property_assignment(self, t):
        """property_assignment : ID COLON expression SEMICOLON
        | ID COLON expression UNIT SEMICOLON
        | NUMBER COLON expression SEMICOLON
        | NUMBER COLON expression UNIT SEMICOLON"""
        name = t[1]
        unit_value = None if len(t) == 5 else unit.get_unit(t[4])
        t[0] = item.Property(name, t[3], unit_value, t.lineno(1))

    def p_graphics_block(self, t):
        "graphics_block : GRAPHICS LBRACE graphics_list RBRACE"
        t[0] = item.GraphicsBlock(t[3][0], t[3][1], t.lineno(1))

    def p_liveryoverride_block(self, t):
        "liveryoverride_block : LIVERYOVERRIDE LPAREN expression RPAREN LBRACE graphics_list RBRACE"
        t[0] = item.LiveryOverride(t[3], item.GraphicsBlock(t[6][0], t[6][1], t.lineno(1)), t.lineno(1))

    def p_graphics_list(self, t):
        """graphics_list : graphics_assignment_list
        | graphics_assignment_list switch_value
        | switch_value"""
        # Save graphics block as a tuple, we need to add position info later
        if len(t) == 2:
            if isinstance(t[1], list):
                t[0] = (t[1], None)
            else:
                t[0] = ([], t[1])
        else:
            t[0] = (t[1], t[2])

    def p_graphics_assignment(self, t):
        "graphics_assignment : expression COLON switch_value"
        t[0] = item.GraphicsDefinition(t[1], t[3])

    def p_graphics_assignment_list(self, t):
        """graphics_assignment_list : graphics_assignment
        | graphics_assignment_list graphics_assignment"""
        if len(t) == 2:
            t[0] = [t[1]]
        else:
            t[0] = t[1] + [t[2]]

    #
    # Program flow control (if/else/while)
    #
    def p_conditional(self, t):
        """conditional : if_else_parts
        | if_else_parts else_block"""
        parts = t[1]
        if len(t) > 2:
            parts.append(t[2])
        t[0] = conditional.ConditionalList(parts)

    def p_else_block(self, t):
        "else_block : ELSE LBRACE script RBRACE"
        t[0] = conditional.Conditional(None, t[3], t.lineno(1))

    def p_if_else_parts(self, t):
        """if_else_parts : IF LPAREN expression RPAREN LBRACE script RBRACE
        | if_else_parts ELSE IF LPAREN expression RPAREN LBRACE script RBRACE"""
        if len(t) == 8:
            t[0] = [conditional.Conditional(t[3], t[6], t.lineno(1))]
        else:
            t[0] = t[1] + [conditional.Conditional(t[5], t[8], t.lineno(2))]

    def p_loop(self, t):
        "loop : WHILE LPAREN expression RPAREN LBRACE script RBRACE"
        t[0] = loop.Loop(t[3], t[6], t.lineno(1))

    #
    # (Random) Switch block
    #
    def p_switch(self, t):
        "switch : SWITCH LPAREN expression_list RPAREN LBRACE switch_body RBRACE"
        t[0] = switch.Switch(t[3], t[6], t.lineno(1))

    def p_switch_body(self, t):
        """switch_body : switch_ranges switch_value
        | switch_ranges"""
        t[0] = switch.SwitchBody(t[1], t[2] if len(t) == 3 else None)

    def p_switch_ranges(self, t):
        """switch_ranges :
        | switch_ranges expression COLON switch_value
        | switch_ranges expression UNIT COLON switch_value
        | switch_ranges expression RANGE expression COLON switch_value
        | switch_ranges expression RANGE expression UNIT COLON switch_value"""
        if len(t) == 1:
            t[0] = []
        elif len(t) == 5:
            t[0] = t[1] + [switch.SwitchRange(t[2], t[2], t[4])]
        elif len(t) == 6:
            t[0] = t[1] + [switch.SwitchRange(t[2], t[2], t[5], t[3])]
        elif len(t) == 7:
            t[0] = t[1] + [switch.SwitchRange(t[2], t[4], t[6])]
        else:
            t[0] = t[1] + [switch.SwitchRange(t[2], t[4], t[7], t[5])]

    def p_switch_value(self, t):
        """switch_value : RETURN expression SEMICOLON
        | RETURN SEMICOLON
        | expression SEMICOLON"""
        if len(t) == 4:
            t[0] = switch.SwitchValue(t[2], True, t[2].pos)
        elif t[1] == "return":
            t[0] = switch.SwitchValue(None, True, t.lineno(1))
        else:
            t[0] = switch.SwitchValue(t[1], False, t[1].pos)

    def p_random_switch(self, t):
        "random_switch : RANDOMSWITCH LPAREN expression_list RPAREN LBRACE random_body RBRACE"
        t[0] = switch.RandomSwitch(t[3], t[6], t.lineno(1))

    def p_random_body(self, t):
        """random_body :
        | random_body expression COLON switch_value"""
        if len(t) == 1:
            t[0] = []
        else:
            t[0] = t[1] + [switch.RandomChoice(t[2], t[4])]

    def p_produce_cargo_list(self, t):
        """produce_cargo_list : LBRACKET RBRACKET
        | LBRACKET setting_value_list RBRACKET"""
        if len(t) == 3:
            t[0] = []
        else:
            t[0] = t[2]

    def p_produce(self, t):
        """produce : PRODUCE LPAREN ID COMMA expression_list RPAREN SEMICOLON
        | PRODUCE LPAREN ID COMMA produce_cargo_list COMMA produce_cargo_list COMMA expression RPAREN
        | PRODUCE LPAREN ID COMMA produce_cargo_list COMMA produce_cargo_list RPAREN"""
        if len(t) == 8:
            t[0] = produce.ProduceOld([t[3]] + t[5], t.lineno(1))
        elif len(t) == 11:
            t[0] = produce.Produce(t[3], t[5], t[7], t[9], t.lineno(1))
        else:
            t[0] = produce.Produce(t[3], t[5], t[7], expression.ConstantNumeric(0), t.lineno(1))

    #
    # Real sprites and related stuff
    #
    def p_real_sprite(self, t):
        """real_sprite : LBRACKET expression_list RBRACKET
        | ID COLON LBRACKET expression_list RBRACKET"""
        if len(t) == 4:
            t[0] = real_sprite.RealSprite(param_list=t[2], poslist=[t.lineno(1)])
        else:
            t[0] = real_sprite.RealSprite(param_list=t[4], label=t[1], poslist=[t.lineno(1)])

    def p_recolour_assignment_list(self, t):
        """recolour_assignment_list :
        | recolour_assignment_list recolour_assignment"""
        t[0] = [] if len(t) == 1 else t[1] + [t[2]]

    def p_recolour_assignment_1(self, t):
        "recolour_assignment : expression COLON expression SEMICOLON"
        t[0] = assignment.Assignment(assignment.Range(t[1], None), assignment.Range(t[3], None), t[1].pos)

    def p_recolour_assignment_2(self, t):
        "recolour_assignment : expression RANGE expression COLON expression RANGE expression SEMICOLON"
        t[0] = assignment.Assignment(assignment.Range(t[1], t[3]), assignment.Range(t[5], t[7]), t[1].pos)

    def p_recolour_assignment_3(self, t):
        "recolour_assignment : expression RANGE expression COLON expression SEMICOLON"
        t[0] = assignment.Assignment(assignment.Range(t[1], t[3]), assignment.Range(t[5], None), t[1].pos)

    def p_recolour_sprite(self, t):
        """real_sprite : RECOLOUR_SPRITE LBRACE recolour_assignment_list RBRACE
        | ID COLON RECOLOUR_SPRITE LBRACE recolour_assignment_list RBRACE"""
        if len(t) == 5:
            t[0] = real_sprite.RecolourSprite(mapping=t[3], poslist=[t.lineno(1)])
        else:
            t[0] = real_sprite.RecolourSprite(mapping=t[5], label=t[1], poslist=[t.lineno(1)])

    def p_template_declaration(self, t):
        "template_declaration : TEMPLATE ID LPAREN id_list RPAREN LBRACE spriteset_contents RBRACE"
        t[0] = spriteblock.TemplateDeclaration(t[2], t[4], t[7], t.lineno(1))

    def p_template_usage(self, t):
        """template_usage : ID LPAREN expression_list RPAREN
        | ID COLON ID LPAREN expression_list RPAREN"""
        if len(t) == 5:
            t[0] = real_sprite.TemplateUsage(t[1], t[3], None, t.lineno(1))
        else:
            t[0] = real_sprite.TemplateUsage(t[3], t[5], t[1], t.lineno(1))

    def p_spriteset_contents(self, t):
        """spriteset_contents : real_sprite
        | template_usage
        | spriteset_contents real_sprite
        | spriteset_contents template_usage"""
        if len(t) == 2:
            t[0] = [t[1]]
        else:
            t[0] = t[1] + [t[2]]

    def p_replace(self, t):
        """replace : REPLACESPRITE LPAREN expression_list RPAREN LBRACE spriteset_contents RBRACE
        | REPLACESPRITE ID LPAREN expression_list RPAREN LBRACE spriteset_contents RBRACE"""
        if len(t) == 9:
            t[0] = replace.ReplaceSprite(t[4], t[7], t[2], t.lineno(1))
        else:
            t[0] = replace.ReplaceSprite(t[3], t[6], None, t.lineno(1))

    def p_replace_new(self, t):
        """replace_new : REPLACENEWSPRITE LPAREN expression_list RPAREN LBRACE spriteset_contents RBRACE
        | REPLACENEWSPRITE ID LPAREN expression_list RPAREN LBRACE spriteset_contents RBRACE"""
        if len(t) == 9:
            t[0] = replace.ReplaceNewSprite(t[4], t[7], t[2], t.lineno(1))
        else:
            t[0] = replace.ReplaceNewSprite(t[3], t[6], None, t.lineno(1))

    def p_base_graphics(self, t):
        """base_graphics : BASE_GRAPHICS LPAREN expression_list RPAREN LBRACE spriteset_contents RBRACE
        | BASE_GRAPHICS ID LPAREN expression_list RPAREN LBRACE spriteset_contents RBRACE"""
        if len(t) == 9:
            t[0] = base_graphics.BaseGraphics(t[4], t[7], t[2], t.lineno(1))
        else:
            t[0] = base_graphics.BaseGraphics(t[3], t[6], None, t.lineno(1))

    def p_font_glyph(self, t):
        """font_glyph : FONTGLYPH LPAREN expression_list RPAREN LBRACE spriteset_contents RBRACE
        | FONTGLYPH ID LPAREN expression_list RPAREN LBRACE spriteset_contents RBRACE"""
        if len(t) == 9:
            t[0] = font.FontGlyphBlock(t[4], t[7], t[2], t.lineno(1))
        else:
            t[0] = font.FontGlyphBlock(t[3], t[6], None, t.lineno(1))

    def p_alt_sprites(self, t):
        "alt_sprites : ALT_SPRITES LPAREN expression_list RPAREN LBRACE spriteset_contents RBRACE"
        t[0] = alt_sprites.AltSpritesBlock(t[3], t[6], t.lineno(1))

    #
    # Sprite sets/groups and such
    #

    def p_spriteset(self, t):
        "spriteset : SPRITESET LPAREN expression_list RPAREN LBRACE spriteset_contents RBRACE"
        t[0] = spriteblock.SpriteSet(t[3], t[6], t.lineno(1))

    def p_spritegroup_normal(self, t):
        "spritegroup : SPRITEGROUP ID LBRACE spriteview_list RBRACE"
        t[0] = spriteblock.SpriteGroup(t[2], t[4], t.lineno(1))

    def p_spritelayout(self, t):
        """spritelayout : SPRITELAYOUT ID LBRACE layout_sprite_list RBRACE
        | SPRITELAYOUT ID LPAREN id_list RPAREN LBRACE layout_sprite_list RBRACE"""
        if len(t) == 6:
            t[0] = spriteblock.SpriteLayout(t[2], [], t[4], t.lineno(1))
        else:
            t[0] = spriteblock.SpriteLayout(t[2], t[4], t[7], t.lineno(1))

    def p_spriteview_list(self, t):
        """spriteview_list :
        | spriteview_list spriteview"""
        if len(t) == 1:
            t[0] = []
        else:
            t[0] = t[1] + [t[2]]

    def p_spriteview(self, t):
        """spriteview : ID COLON LBRACKET expression_list RBRACKET SEMICOLON
        | ID COLON expression SEMICOLON"""
        if len(t) == 7:
            t[0] = spriteblock.SpriteView(t[1], t[4], t.lineno(1))
        else:
            t[0] = spriteblock.SpriteView(t[1], [t[3]], t.lineno(1))

    def p_layout_sprite_list(self, t):
        """layout_sprite_list :
        | layout_sprite_list layout_sprite"""
        if len(t) == 1:
            t[0] = []
        else:
            t[0] = t[1] + [t[2]]

    def p_layout_sprite(self, t):
        "layout_sprite : ID LBRACE layout_param_list RBRACE"
        t[0] = spriteblock.LayoutSprite(t[1], t[3], t.lineno(1))

    def p_layout_param_list(self, t):
        """layout_param_list : assignment
        | layout_param_list assignment"""
        if len(t) == 2:
            t[0] = [t[1]]
        else:
            t[0] = t[1] + [t[2]]

    #
    # Town names
    #
    def p_town_names(self, t):
        """town_names : TOWN_NAMES LPAREN expression RPAREN LBRACE town_names_param_list RBRACE
        | TOWN_NAMES LBRACE town_names_param_list RBRACE"""
        if len(t) == 8:
            t[0] = townnames.TownNames(t[3], t[6], t.lineno(1))
        else:
            t[0] = townnames.TownNames(None, t[3], t.lineno(1))

    def p_town_names_param_list(self, t):
        """town_names_param_list : town_names_param
        | town_names_param_list town_names_param"""
        if len(t) == 2:
            t[0] = [t[1]]
        else:
            t[0] = t[1] + [t[2]]

    def p_town_names_param(self, t):
        """town_names_param : ID COLON string SEMICOLON
        | LBRACE town_names_part_list RBRACE
        | LBRACE town_names_part_list COMMA RBRACE"""
        if t[1] != "{":
            t[0] = townnames.TownNamesParam(t[1], t[3], t.lineno(1))
        else:
            t[0] = townnames.TownNamesPart(t[2], t.lineno(1))

    def p_town_names_part_list(self, t):
        """town_names_part_list : town_names_part
        | town_names_part_list COMMA town_names_part"""
        if len(t) == 2:
            t[0] = [t[1]]
        else:
            t[0] = t[1] + [t[3]]

    def p_town_names_part(self, t):
        """town_names_part : TOWN_NAMES LPAREN expression COMMA expression RPAREN
        | ID LPAREN STRING_LITERAL COMMA expression RPAREN"""
        if t[1] == "town_names":
            t[0] = townnames.TownNamesEntryDefinition(t[3], t[5], t.lineno(1))
        else:
            t[0] = townnames.TownNamesEntryText(t[1], t[3], t[5], t.lineno(1))

    #
    # Snow line
    #
    def p_snowline(self, t):
        "snowline : SNOWLINE LPAREN ID RPAREN LBRACE snowline_assignment_list RBRACE"
        t[0] = snowline.Snowline(t[3], t[6], t.lineno(1))

    #
    # Various misc. main script blocks that don't belong anywhere else
    #
    def p_param_assignment(self, t):
        "param_assignment : expression EQ expression SEMICOLON"
        t[0] = actionD.ParameterAssignment(t[1], t[3])

    def p_error_block(self, t):
        "error_block : ERROR LPAREN expression_list RPAREN SEMICOLON"
        t[0] = error.Error(t[3], t.lineno(1))

    def p_disable_item(self, t):
        "disable_item : DISABLE_ITEM LPAREN expression_list RPAREN SEMICOLON"
        t[0] = disable_item.DisableItem(t[3], t.lineno(1))

    def p_cargotable(self, t):
        """cargotable : CARGOTABLE LBRACE cargotable_list RBRACE
        | CARGOTABLE LBRACE cargotable_list COMMA RBRACE"""
        t[0] = cargotable.CargoTable(t[3], t.lineno(1))

    def p_cargotable_list(self, t):
        """cargotable_list : ID
        | STRING_LITERAL
        | cargotable_list COMMA ID
        | cargotable_list COMMA STRING_LITERAL"""
        if len(t) == 2:
            t[0] = [t[1]]
        else:
            t[0] = t[1] + [t[3]]

    def p_railtypetable(self, t):
        """railtype : RAILTYPETABLE LBRACE tracktypetable_list RBRACE
        | RAILTYPETABLE LBRACE tracktypetable_list COMMA RBRACE"""
        t[0] = tracktypetable.RailtypeTable(t[3], t.lineno(1))

    def p_roadtypetable(self, t):
        """roadtype : ROADTYPETABLE LBRACE tracktypetable_list RBRACE
        | ROADTYPETABLE LBRACE tracktypetable_list COMMA RBRACE"""
        t[0] = tracktypetable.RoadtypeTable(t[3], t.lineno(1))

    def p_tramtypetable(self, t):
        """tramtype : TRAMTYPETABLE LBRACE tracktypetable_list RBRACE
        | TRAMTYPETABLE LBRACE tracktypetable_list COMMA RBRACE"""
        t[0] = tracktypetable.TramtypeTable(t[3], t.lineno(1))

    def p_tracktypetable_list(self, t):
        """tracktypetable_list : tracktypetable_item
        | tracktypetable_list COMMA tracktypetable_item"""
        if len(t) == 2:
            t[0] = [t[1]]
        else:
            t[0] = t[1] + [t[3]]

    def p_tracktypetable_item(self, t):
        """tracktypetable_item : ID
        | STRING_LITERAL
        | ID COLON LBRACKET expression_list RBRACKET"""
        if len(t) == 2:
            t[0] = t[1]
        else:
            t[0] = assignment.Assignment(t[1], t[4], t[1].pos)

    def p_basecost(self, t):
        "basecost : BASECOST LBRACE generic_assignment_list RBRACE"
        t[0] = basecost.BaseCost(t[3], t.lineno(1))

    def p_deactivate(self, t):
        "deactivate : DEACTIVATE LPAREN expression_list RPAREN SEMICOLON"
        t[0] = deactivate.DeactivateBlock(t[3], t.lineno(1))

    def p_grf_block(self, t):
        "grf_block : GRF LBRACE assignment_list RBRACE"
        t[0] = grf.GRF(t[3], t.lineno(1))

    def p_skip_all(self, t):
        "skip_all : SKIP_ALL SEMICOLON"
        t[0] = skipall.SkipAll(t.lineno(1))

    def p_engine_override(self, t):
        "engine_override : ENGINE_OVERRIDE LPAREN expression_list RPAREN SEMICOLON"
        t[0] = override.EngineOverride(t[3], t.lineno(1))

    def p_sort_vehicles(self, t):
        "sort_vehicles : SORT_VEHICLES LPAREN expression_list RPAREN SEMICOLON"
        t[0] = sort_vehicles.SortVehicles(t[3], t.lineno(1))

    def p_tilelayout(self, t):
        "tilelayout : TILELAYOUT ID LBRACE tilelayout_list RBRACE"
        t[0] = tilelayout.TileLayout(t[2], t[4], t.lineno(1))

    def p_tilelayout_list(self, t):
        """tilelayout_list : tilelayout_item
        | tilelayout_list tilelayout_item"""
        if len(t) == 2:
            t[0] = [t[1]]
        else:
            t[0] = t[1] + [t[2]]

    def p_tilelayout_item_tile(self, t):
        "tilelayout_item : expression COMMA expression COLON expression SEMICOLON"
        t[0] = tilelayout.LayoutTile(t[1], t[3], t[5])

    def p_tilelayout_item_prop(self, t):
        "tilelayout_item : assignment"
        t[0] = t[1]

    def p_constant(self, t):
        "constant : CONST expression EQ expression SEMICOLON"
        t[0] = constant.Constant(t[2], t[4])
