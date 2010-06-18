from nml import expression, generic, global_constants, grfstrings, unit
from nml.actions import action0, action1, action2var, action3, action5, action7, action8, actionA, actionB, actionD, actionE, actionF, action12, real_sprite
from actions.sprite_count import SpriteCountAction

def print_script(script, indent):
    for r in script:
        r.debug_print(indent)

feature_ids = {
    'FEAT_TRAINS': 0x00,
    'FEAT_ROADVEHS': 0x01,
    'FEAT_SHIPS': 0x02,
    'FEAT_AIRCRAFTS': 0x03,
    'FEAT_STATIONS': 0x04,
    'FEAT_CANALS': 0x05,
    'FEAT_BRIDGES': 0x06,
    'FEAT_HOUSES': 0x07,
    'FEAT_GLOBALVARS': 0x08,
    'FEAT_INDUSTRYTILES': 0x09,
    'FEAT_INDUSTRIES': 0x0A,
    'FEAT_CARGOS': 0x0B,
    'FEAT_SOUNDEFFECTS': 0x0C,
    'FEAT_AIRPORTS': 0x0D,
    'FEAT_SIGNALS': 0x0E,
    'FEAT_OBJECTS': 0x0F,
    'FEAT_RAILTYPES': 0x10,
    'FEAT_AIRPORTTILES': 0x11,
}

########### code blocks ###########
class GRF(object):
    def __init__(self, alist):
        self.name = None
        self.desc = None
        self.grfid = None
        for assignment in alist:
            if assignment.name.value == "grfid":
                if not isinstance(assignment.value, expression.StringLiteral):
                    raise generic.ScriptError("GRFID must be a string literal")
            elif not isinstance(assignment.value, expression.String):
                raise generic.ScriptError("Assignments in GRF-block must be constant strings")
            if assignment.name.value == "name": self.name = assignment.value
            elif assignment.name.value == "desc": self.desc = assignment.value
            elif assignment.name.value == "grfid": self.grfid = assignment.value
            else: raise generic.ScriptError("Unknown item in GRF-block: " + assignment.name)

    def debug_print(self, indentation):
        print indentation*' ' + 'GRF'
        if self.grfid is not None:
            print (2+indentation)*' ' + 'grfid:', self.grfid.value
        if self.name is not None:
            print (2+indentation)*' ' + 'Name:'
            self.name.debug_print(indentation + 4)
        if self.desc is not None:
            print (2+indentation)*' ' + 'Description:'
            self.desc.debug_print(indentation + 4)

    def get_action_list(self):
        return [action8.Action8(self.grfid, self.name, self.desc)]

    def __str__(self):
        ret = 'grf {\n'
        ret += '\tgrfid: %s;\n' % str(self.grfid)
        if self.name is not None:
            ret += '\tname: %s;\n' % str(self.name)
        if self.desc is not None:
            ret += '\tdesc: %s;\n' % str(self.desc)
        ret += '}\n'
        return ret

class Assignment(object):
    def __init__(self, name, value):
        self.name = name
        self.value = value

    def debug_print(self, indentation):
        print indentation*' ' + 'Assignment, name = ', self.name
        self.value.debug_print(indentation + 2)

class Conditional(object):
    def __init__(self, expr, block, else_block = None):
        self.expr = expr
        if self.expr is not None:
            self.expr = self.expr.reduce(global_constants.const_list)
        self.block = block
        self.else_block = else_block

    def debug_print(self, indentation):
        print indentation*' ' + 'Conditional'
        if self.expr is not None:
            print (2+indentation)*' ' + 'Expression:'
            self.expr.debug_print(indentation + 4)
        print (2+indentation)*' ' + 'Block:'
        print_script(self.block, indentation + 4)
        if self.else_block is not None:
            print (indentation)*' ' + 'Else block:'
            self.else_block.debug_print(indentation)

    def get_action_list(self):
        return action7.parse_conditional_block(self)

    def __str__(self):
        ret = ''
        if self.expr is not None:
            ret += 'if (%s) {\n' % str(self.expr)
        for b in self.block:
            ret += '\t' + str(b).replace('\n', '\n\t')[0:-1]
        if self.expr is not None:
            if self.else_block is not None:
                ret += '} else {\n'
                ret += str(self.else_block)
            ret += '}\n'
        return ret

class Loop(object):
    def __init__(self, expr, block):
        self.expr = expr
        self.block = block

    def debug_print(self, indentation):
        print indentation*' ' + 'While loop'
        print (2+indentation)*' ' + 'Expression:'
        self.expr.debug_print(indentation + 4)
        print (2+indentation)*' ' + 'Block:'
        print_script(self.block, indentation + 4)

    def get_action_list(self):
        return action7.parse_loop_block(self)

    def __str__(self):
        ret = 'while(%s) {\n' % self.expr
        for b in self.block:
            ret += '\t' + str(b).replace('\n', '\n\t')[0:-1]
        ret += '}\n'
        return ret

var_ranges = {
    'SELF' : 0x89,
    'PARENT' : 0x8A
}

class Switch(object):
    def __init__(self, feature, var_range, name, expr, body):
        self.feature = feature.reduce_constant([feature_ids])
        if var_range.value in var_ranges:
            self.var_range = var_ranges[var_range.value]
        else:
            raise generic.ScriptError("Unrecognized value for switch parameter 2 'variable range': '%s'" % var_range.value)
        self.name = name
        self.expr = expr
        self.body = body

    def debug_print(self, indentation):
        print indentation*' ' + 'Switch, Feature =',self.feature.value,', name =', self.name.value
        print (2+indentation)*' ' + 'Expression:'
        self.expr.debug_print(indentation + 4)
        print (2+indentation)*' ' + 'Body:'
        self.body.debug_print(indentation + 4)

    def get_action_list(self):
        return action2var.parse_varaction2(self)

    def __str__(self):
        var_range = 'SELF' if self.var_range == 0x89 else 'PARENT'
        return 'switch(%s, %s, %s, %s) {\n%s}\n' % (str(self.feature), var_range, str(self.name), str(self.expr), str(self.body))


class SwitchBody(object):
    def __init__(self, ranges, default):
        self.ranges = ranges
        self.default = default

    def debug_print(self, indentation):
        for r in self.ranges:
            r.debug_print(indentation)
        print indentation*' ' + 'Default:'
        if isinstance(self.default, expression.Identifier):
            print (indentation+2)*' ' + 'Go to switch:'
            self.default.debug_print(indentation + 4);
        elif self.default is None:
            print (indentation+2)*' ' + 'Return computed value'
        else:
            self.default.debug_print(indentation + 2)

    def __str__(self):
        ret = ''
        for r in self.ranges:
            ret += '\t%s\n' % str(r)
        if self.default is None:
            ret += '\treturn;\n'
        else:
            ret += '\t%s;\n' % str(self.default)
        return ret

class DeactivateBlock(object):
    def __init__(self, grfid_list):
        self.grfid_list = [grfid.reduce() for grfid in grfid_list]

    def debug_print(self, indentation):
        print indentation*' ' + 'Deactivate other newgrfs:'
        for grfid in self.grfid_list:
            grfid.debug_print(indentation + 2)

    def get_action_list(self):
        return actionE.parse_deactivate_block(self)

def validate_item_block(block_list):
    for block in block_list:
        if isinstance(block, PropertyBlock): continue
        if isinstance(block, GraphicsBlock): continue
        if isinstance(block, LiveryOverride): continue
        if isinstance(block, Conditional):
            while block is not None:
                validate_item_block(block.block)
                block = block.else_block
            continue
        if isinstance(block, Loop):
            validate_item_block(block.body)
            continue
        raise generic.ScriptError("Invalid block type inside 'Item'-block")

item_feature = None
item_id = None

class Item(object):
    def __init__(self, params, body):
        if len(params) >= 1:
            self.feature = params[0].reduce_constant([feature_ids])
        else:
            raise generic.ScriptError("Item block requires at least one parameter, got 0")
        if len(params) > 3:
            raise generic.ScriptError("Item block requires at most 3 parameters, found %d" % len(params))

        if len(params) == 3:
            self.id = params[2].reduce_constant()
        else:
            self.id = None

        if len(params) >= 2:
            self.name = params[1]
            if not isinstance(self.name, expression.Identifier):
                raise generic.ScriptError("Item parameter 2 'name' should be an identifier")
            if self.name.value in expression.item_names:
                id = expression.ConstantNumeric(expression.item_names[self.name.value])
                if self.id is not None and id.value != self.id.value:
                    raise generic.ScriptError("Item with name '%s' has already been assigned to id %d, cannot reassign to id %d" % (self.name.value, self.id.value, id.value))
                self.id = id
        else:
            self.name = None

        if self.id is None:
            self.id = expression.ConstantNumeric(action0.get_free_id(self.feature.value))
        if self.name is not None:
            expression.item_names[self.name.value] = self.id.value

        self.body = body
        validate_item_block(body)

    def debug_print(self, indentation):
        print indentation*' ' + 'Item, feature', hex(self.feature.value)
        for b in self.body: b.debug_print(indentation + 2)

    def get_action_list(self):
        global item_feature, item_id
        item_id = self.id
        item_feature = self.feature.value
        action_list = []
        for b in self.body:
            action_list.extend(b.get_action_list())
        return action_list

    def __str__(self):
        ret = 'item(%d' % self.feature.value
        if self.name is not None:
            ret += ', %s, %s' % (str(self.name), str(self.id))
        ret += ') {\n'
        for b in self.body:
            ret += '\t' + str(b).replace('\n', '\n\t')[0:-1]
        ret += '}\n'
        return ret

class Unit(object):
    def __init__(self, name):
        assert name in unit.units
        self.name = name
        self.type = unit.units[name]['type']
        self.convert = unit.units[name]['convert']

    def __str__(self):
        return self.name

class Property(object):
    def __init__(self, name, value, unit):
        self.name = name
        self.value = value.reduce(global_constants.const_list)
        self.unit = unit
        if unit is not None and not (isinstance(self.value, expression.ConstantNumeric) or isinstance(self.value, expression.ConstantFloat)):
            raise generic.ScriptError("Using a unit for a property is only allowed if the value is constant")

    def debug_print(self, indentation):
        print indentation*' ' + 'Property:', self.name.value
        self.value.debug_print(indentation + 2)

    def __str__(self):
        unit = '' if self.unit is None else ' ' + str(self.unit)
        return '\t%s: %s%s;' % (self.name, self.value, unit)

class PropertyBlock(object):
    def __init__(self, prop_list):
        self.prop_list = prop_list

    def debug_print(self, indentation):
        print indentation*' ' + 'Property block:'
        for prop in self.prop_list:
            prop.debug_print(indentation + 2)

    def get_action_list(self):
        global item_feature, item_id
        return action0.parse_property_block(self.prop_list, item_feature, item_id)

    def __str__(self):
        ret = 'property {\n'
        for prop in self.prop_list:
            ret += '%s\n' % str(prop)
        ret += '}\n'
        return ret

class LiveryOverride(object):
    def __init__(self, wagon_id, graphics_block):
        self.graphics_block = graphics_block
        self.wagon_id = wagon_id

    def debug_print(self, indentation):
        print indentation*' ' + 'Liverry override, wagon id:'
        self.wagon_id.debug_print(indentation + 2)
        for graphics in self.graphics_block.graphics_list:
            graphics.debug_print(indentation + 2)
        print (indentation+2)*' ' + 'Default graphics:', self.graphics_block.default_graphics

    def get_action_list(self):
        global item_feature
        wagon_id = self.wagon_id.reduce_constant([expression.item_names])
        return action3.parse_graphics_block(self.graphics_block.graphics_list, self.graphics_block.default_graphics, item_feature, wagon_id, True)

class GraphicsBlock(object):
    def __init__(self, graphics_list, default_graphics):
        self.graphics_list = graphics_list
        self.default_graphics = default_graphics

    def debug_print(self, indentation):
        print indentation*' ' + 'Graphics block:'
        for graphics in self.graphics_list:
            graphics.debug_print(indentation + 2)
        print (indentation+2)*' ' + 'Default graphics:', self.default_graphics

    def get_action_list(self):
        global item_feature, item_id
        return action3.parse_graphics_block(self.graphics_list, self.default_graphics, item_feature, item_id)

class GraphicsDefinition(object):
    def __init__(self, cargo_id, action2_id):
        self.cargo_id = cargo_id
        self.action2_id = action2_id

    def debug_print(self, indentation):
        print indentation*' ' + 'Graphics:'
        print (indentation+2)*' ' + 'Cargo:', self.cargo_id.value
        print (indentation+2)*' ' + 'Linked to action2:', self.action2_id.value

class ReplaceSprite(object):
    def __init__(self, start_id, pcx, sprite_list):
        self.start_id = start_id.reduce_constant()
        self.pcx = pcx
        self.sprite_list = sprite_list

    def debug_print(self, indentation):
        print indentation*' ' + 'Replace sprites starting at', self.start_id
        print (indentation+2)*' ' + 'Source:', self.pcx.value
        print (indentation+2)*' ' + 'Sprites:'
        for sprite in self.sprite_list:
            sprite.debug_print(indentation + 4)

    def get_action_list(self):
        return actionA.parse_actionA(self)

class ReplaceNewSprite(object):
    def __init__(self, type, pcx, offset, sprite_list):
        self.type = type
        self.pcx = pcx
        self.offset = offset
        self.sprite_list = sprite_list

    def debug_print(self, indentation):
        print indentation*' ' + 'Replace sprites for new features of type', self.type
        print (indentation+2)*' ' + 'Offset:  ', self.offset
        print (indentation+2)*' ' + 'Source:  ', self.pcx.value
        print (indentation+2)*' ' + 'Sprites:'
        for sprite in self.sprite_list:
            sprite.debug_print(indentation + 4)

    def get_action_list(self):
        return action5.parse_action5(self)

class FontGlyphBlock(object):
    def __init__(self, font_size, base_char, pcx, sprite_list):
        self.font_size = font_size
        self.base_char = base_char
        self.pcx = pcx
        self.sprite_list = sprite_list

    def debug_print(self, indentation):
        print indentation*' ' + 'Load font glpyhs, starting at', self.base_char
        print (indentation+2)*' ' + 'Font size:  ', self.font_size
        print (indentation+2)*' ' + 'Source:  ', self.pcx.value
        print (indentation+2)*' ' + 'Sprites:'
        for sprite in self.sprite_list:
            sprite.debug_print(indentation + 4)

    def get_action_list(self):
        return action12.parse_action12(self)

class SpriteBlock(object):
    def __init__(self, feature, spriteset_list):
        self.feature = feature.reduce_constant([feature_ids])
        self.spriteset_list = spriteset_list

    def debug_print(self, indentation):
        print indentation*' ' + 'Sprite block, feature', hex(self.feature.value)
        for spriteset in self.spriteset_list:
            spriteset.debug_print(indentation + 2)
    def get_action_list(self):
        return action1.parse_sprite_block(self)

class TemplateDeclaration(object):
    def __init__(self, name, param_list, sprite_list):
        self.name = name
        self.param_list = param_list
        self.sprite_list = sprite_list

    def debug_print(self, indentation):
        print indentation*' ' + 'Template declaration:', self.name.value
        print (indentation+2)*' ' + 'Parameters:'
        for param in self.param_list:
            param.debug_print(indentation + 4)
        print (indentation+2)*' ' + 'Sprites:'
        for sprite in self.sprite_list:
            sprite.debug_print(indentation + 4)

    def get_action_list(self):
        #check that all templates that are referred to exist at this point
        #This prevents circular dependencies
        for sprite in self.sprite_list:
            if isinstance(sprite, real_sprite.TemplateUsage):
                if sprite.name.value == self.name.value:
                    raise generic.ScriptError("Sprite template '%s' includes itself." % sprite.name.value)
                elif sprite.name.value not in real_sprite.sprite_template_map:
                    raise generic.ScriptError("Encountered unknown template identifier: " + sprite.name.value)
        #Register template
        if self.name.value not in real_sprite.sprite_template_map:
            real_sprite.sprite_template_map[self.name.value] = self
        else:
            raise generic.ScriptError("Template named '" + self.name.value + "' is already defined")
        return []

class SpriteView(object):
    def __init__(self, name, spriteset_list):
        self.name = name
        self.spriteset_list = spriteset_list

    def debug_print(self, indentation):
        print indentation*' ' + 'Sprite view:', self.name.value
        print (indentation+2)*' ' + 'Sprite sets:'
        for spriteset in self.spriteset_list:
            spriteset.debug_print(indentation + 4)

class LayoutSprite(object):
    def __init__(self, type, param_list):
        self.type = type
        self.param_list = param_list

    def debug_print(self, indentation):
        print indentation*' ' + 'Tile layout sprite of type:', self.type
        for layout_param in self.param_list:
            layout_param.debug_print(indentation + 2)

class LayoutParam(object):
    def __init__(self, name, value):
        self.name = name
        self.value = value.reduce(global_constants.const_list, False)

    def debug_print(self, indentation):
        print indentation*' ' + 'Layout parameter:', self.name.value
        if isinstance(self.value, basestring):
            print (indentation + 2)*' ' + 'String: ', self.value
        else:
            self.value.debug_print(indentation + 2)


class TownNames(object):
    """
    town_names ast node.

    @ivar name: Name ID of the town_name.
    @type name: C{None}, L{Identifier}, or L{ConstantNumeric}

    @ivar id_number: Allocated ID number for this town_name action F node.
    @type id_number: C{None} or C{int}

    @ivar style_name: Name of the translated string containing the name of the style, if any.
    @type style_name: C{None} or L{Identifier}

    @ivar style_names: List translations of L{style_name}, pairs (languageID, text).
    @type style_names: C{list} of (C{int}, L{Identifier})

    @ivar parts: Parts of the names.
    @type parts: C{list} of L{TownNamesPart}

    @ivar free_bit: First available bit above the bits used by this block.
    @type free_bit: C{None} if unset, else C{int}

    @ivar pos: Position information of the 'town_names' block.
    @type pos: L{Position}
    """
    def __init__(self, name, param_list, pos):
        self.name = name
        self.id_number = None
        self.style_name = None
        self.style_names = []
        self.parts = []
        self.free_bit = None
        self.pos = pos

        for param in param_list:
            if isinstance(param, TownNamesPart): self.parts.append(param)
            else:
                if param.key.value != 'styles':
                    raise generic.ScriptError("Expected 'styles' keyword.", param.pos)
                if len(param.value.params) > 0:
                    raise generic.ScriptError("Parameters of the 'styles' were not expected.", param.pos)
                if self.style_name is not None:
                    raise generic.ScriptError("'styles' is already defined.", self.pos)
                self.style_name = param.value.name.value

        if len(self.parts) == 0:
            raise generic.ScriptError("Missing name parts in a town_names item.", self.pos)

        # 'name' is actually a number.
        # Allocate it now, before the self.prepare_output() call (to prevent names to grab it).
        if self.name is not None and not isinstance(self.name, expression.Identifier):
            value = self.name.reduce_constant()
            if not isinstance(value, expression.ConstantNumeric):
                raise generic.ScriptError("ID should be an integer number.", self.pos)

            self.id_number = value.value
            if self.id_number < 0 or self.id_number > 0x7f:
                raise generic.ScriptError("ID must be a number between 0 and 0x7f (inclusive)", self.pos)

            if self.id_number not in actionF.free_numbers:
                raise generic.ScriptError("town names ID 0x%x is already used." % self.id_number, self.pos)
            actionF.free_numbers.remove(self.id_number)

    def prepare_output(self):
        # Resolve references to earlier townname actions
        blocks = set()
        for part in self.parts:
            blocks.update(part.resolve_townname_id())

        # Allocate a number for this action F.
        if self.name is None or isinstance(self.name, expression.Identifier):
            self.id_number = actionF.get_free_id()
            if isinstance(self.name, expression.Identifier):
                if self.name.value in actionF.named_numbers:
                    raise generic.ScriptError('Cannot define town name "%s", it is already in use' % self.name, self.pos)
                actionF.named_numbers[self.name.value] = self.id_number # Add name to the set 'safe' names.
        else: actionF.numbered_numbers.add(self.id_number) # Add number to the set of 'safe' numbers.

        actionF.town_names_blocks[self.id_number] = self # Add self to the available blocks.

        # Ask descendants for the lowest available bit.
        if len(blocks) == 0: startbit = 0 # No descendants, all bits are free.
        else: startbit = max(actionF.town_names_blocks[block].free_bit for block in blocks)
        # Allocate random bits to all parts.
        for part in self.parts:
            num_bits = part.assign_bits(startbit)
            startbit += num_bits
        self.free_bit = startbit

        if startbit > 32:
            raise generic.ScriptError("Not enough random bits for the town name generation (%d needed, 32 available)" % startbit, self.pos)

        # Pull style names if needed.
        if self.style_name is not None:
            if self.style_name not in grfstrings.grf_strings:
                raise generic.ScriptError("Unknown string: " + self.style_name)
            self.style_names = [(transl['lang'], transl['text']) for transl in grfstrings.grf_strings[self.style_name]]
            self.style_names.sort()
            if len(self.style_names) == 0:
                raise generic.ScriptError('Style "%s" defined, but no translations found for it' % self.style_name, self.pos)
        else: self.style_names = []


    def get_id(self):
        return self.id_number | (0x80 if len(self.style_names) > 0 else 0)

    # Style names
    def get_length_styles(self):
        if len(self.style_names) == 0: return 0
        size = 0
        for _lang, txt in self.style_names:
            size += 1 + 2 + grfstrings.get_string_size(txt) + 1 # Language ID, text, 0 byte
        return size + 1 # Terminating 0

    def write_styles(self, file):
        if len(self.style_names) == 0: return

        for lang, txt in self.style_names:
            file.print_bytex(lang)
            file.print_string(txt, final_zero = True)
        file.print_bytex(0)

    # Parts
    def get_length_parts(self):
        size = 1 # num_parts byte
        return size + sum(part.get_length() for part in self.parts)

    def write_parts(self, file):
        file.print_bytex(len(self.parts))
        for part in self.parts:
            part.write(file)
            file.newline()


    def debug_print(self, indentation):
        if isinstance(self.name, basestring):
            name_text = "name = " + repr(self.name)
            if self.id_number is not None: name_text += " (allocated number is 0x%x)" % self.id_number
        elif self.id_number is not None:
            name_text = "number = 0x%x" % self.id_number
        else:
            name_text = "(unnamed)"

        print indentation*' ' + 'Town name ' + name_text
        if self.style_name is not None:
            print indentation*' ' + "  style name string:", self.style_name
        for part in self.parts:
            print indentation*' ' + "-name part:"
            part.debug_print(indentation + 2)

    def get_action_list(self):
        return [actionF.ActionF(self)]


class TownNamesPart(object):
    """
    A class containing a town name part.

    @ivar pieces: Pieces of the town name part.
    @type pieces: C{list}

    @ivar pos: Position information of the parts block.
    @type pos: L{Position}
    """
    def __init__(self, pieces, pos):
        self.pos = pos
        self.pieces = pieces
        if len(self.pieces) == 0:
            raise generic.ScriptError("Expected names and/or town_name references in the part.", self.pos)

        self.total = sum(piece.probability.value for piece in self.pieces)
        self.startbit = None
        self.num_bits = 0

    def assign_bits(self, startbit):
        """
        Assign bits for this piece.

        @param startbit: First bit free for use.
        @return: Number of bits needed for this piece.
        """
        self.startbit = startbit
        n = 1
        while self.total > (1 << n): n = n + 1
        self.num_bits = n
        return n

    def debug_print(self, indentation):
        print indentation*' ' + 'Town names part (total %d)' % self.total
        for piece in self.pieces:
            piece.debug_print(indentation + 2, self.total)

    def get_length(self):
        size = 3 # textcount, firstbit, bitcount bytes.
        size += sum(piece.get_length() for piece in self.pieces)
        return size

    def resolve_townname_id(self):
        '''
        Resolve the reference numbers to previous C{town_names} blocks.

        @return: Set of referenced C{town_names} block numbers.
        '''
        if len(self.pieces) == 0:
            raise generic.ScriptError("Expected at least one value in a part.", self.pos)
        if len(self.pieces) > 255:
            raise generic.ScriptError("Too many values in a part, found %d, maximum is 255" % len(self.pieces), self.pos)
        blocks = set()
        for piece in self.pieces:
            block = piece.resolve_townname_id()
            if block is not None: blocks.add(block)
        return blocks

    def write(self, file):
        file.print_bytex(len(self.pieces))
        file.print_bytex(self.startbit)
        file.print_bytex(self.num_bits)
        for piece in self.pieces:
            piece.write(file)


class TownNamesParam(object):
    """
    Class containing a parameter of a town name.
    Currently known key/values:
     - 'styles'  / string expression
    """
    def __init__(self, key, value, pos):
        self.key = key
        self.value = value
        self.pos = pos

class TownNamesEntryDefinition(object):
    """
    An entry in a part referring to a non-final town name, with a given probability.

    @ivar def_number: Name or number referring to a previous town_names node.
    @type def_number: L{Identifier} or L{ConstantNumeric}

    @ivar number: Actual ID to use.
    @type number: C{None} or C{int}

    @ivar probability: Probability of picking this reference.
    @type probability: C{ConstantNumeric}

    @ivar pos: Position information of the parts block.
    @type pos: L{Position}
    """
    def __init__(self, def_number, probability, pos):
        self.def_number = def_number
        self.number = None
        self.pos = pos
        if not isinstance(self.def_number, expression.Identifier):
            self.def_number = self.def_number.reduce_constant()
            if not isinstance(self.def_number, expression.ConstantNumeric):
                raise generic.ScriptError("Reference to other town name ID should be an integer number.", self.pos)
            if self.def_number.value < 0 or self.def_number.value > 0x7f:
                raise generic.ScriptError("Reference number out of range (must be between 0 and 0x7f inclusive).", self.pos)

        self.probability = probability.reduce_constant()
        if not isinstance(self.probability, expression.ConstantNumeric):
            raise generic.ScriptError("Probability should be an integer number.", self.pos)
        if self.probability.value < 0 or self.probability.value > 0x7f:
            raise generic.ScriptError("Probability out of range (must be between 0 and 0x7f inclusive).", self.pos)

    def debug_print(self, indentation, total):
        if isinstance(self.def_number, expression.Identifier): name_text = "name '" + self.def_number.value + "'"
        else: name_text = "number 0x%x" % self.def_number.value
        print indentation*' ' + ('Insert town_name ID %s with probability %d/%d' % (name_text, self.probability.value, total))

    def get_length(self):
        return 2

    def resolve_townname_id(self):
        '''
        Resolve the reference number to a previous C{town_names} block.

        @return: Number of the referenced C{town_names} block.
        '''
        if isinstance(self.def_number, expression.Identifier):
            self.number = actionF.named_numbers.get(self.def_number.value)
            if self.number is None:
                raise generic.ScriptError('Town names name "%s" is not defined or points to a next town_names node' % self.def_number.value, self.pos)
        else:
            self.number = self.def_number.value
            if self.number not in actionF.numbered_numbers:
                raise generic.ScriptError('Town names number "%s" is not defined or points to a next town_names node' % self.number, self.pos)
        return self.number

    def write(self, file):
        file.print_bytex(self.probability.value | 0x80)
        file.print_bytex(self.number)

class TownNamesEntryText(object):
    """
    An entry in a part, a text-string with a given probability.

    @ivar pos: Position information of the parts block.
    @type pos: L{Position}
    """
    def __init__(self, id, text, probability, pos):
        self.pos = pos
        if id.value != 'text':
            raise generic.ScriptError("Expected 'text' prefix.")

        self.text = text
        if not isinstance(self.text, expression.StringLiteral):
            raise generic.ScriptError("Expected string literal for the name.", self.pos)

        self.probability = probability.reduce_constant()
        if not isinstance(self.probability, expression.ConstantNumeric):
            raise generic.ScriptError("Probability should be an integer number.", self.pos)
        if self.probability.value < 0 or self.probability.value > 0x7f:
            raise generic.ScriptError("Probability out of range (must be between 0 and 0x7f inclusive).", self.pos)

    def debug_print(self, indentation, total):
        print indentation*' ' + ('Text %s with probability %d/%d' % (self.text.value, self.probability.value, total))

    def get_length(self):
        return 1 + 2 + grfstrings.get_string_size(self.text.value) + 1 # probability, text, 0

    def resolve_townname_id(self):
        '''
        Resolve the reference number to a previous C{town_names} block.

        @return: C{None}, as being the block number of a referenced previous C{town_names} block.
        '''
        return None

    def write(self, file):
        file.print_bytex(self.probability.value)
        file.print_string(self.text.value, final_zero = True)


class Error(object):
    def __init__(self, param_list):
        self.params = []
        if not 2 <= len(param_list) <= 5:
            raise generic.ScriptError("'error' expects between 2 and 5 parameters, got " + str(len(param_list)))
        self.severity = param_list[0].reduce([actionB.error_severity])
        self.msg      = param_list[1]
        self.data     = param_list[2] if len(param_list) >= 3 else None
        self.params.append(param_list[3].reduce() if len(param_list) >= 4 else None)
        self.params.append(param_list[4].reduce() if len(param_list) >= 5 else None)

    def debug_print(self, indentation):
        print indentation*' ' + 'Error message'
        print (indentation+2)*' ' + 'Message:'
        self.msg.debug_print(indentation + 4)
        print (indentation+2)*' ' + 'Severity:'
        self.severity.debug_print(indentation + 4)
        print (indentation+2)*' ' + 'Data: '
        if self.data is not None: self.data.debug_print(indentation + 4)
        print (indentation+2)*' ' + 'Param1: '
        if self.params[0] is not None: self.params[0].debug_print(indentation + 4)
        print (indentation+2)*' ' + 'Param2: '
        if self.params[1] is not None: self.params[1].debug_print(indentation + 4)

    def get_action_list(self):
        return actionB.parse_error_block(self)

class CargoTable(object):
    def __init__(self, cargo_list):
        self.cargo_list = cargo_list
        for i, cargo in enumerate(cargo_list):
            global_constants.cargo_numbers[cargo.value] = i

    def debug_print(self, indentation):
        print indentation*' ' + 'Cargo table'
        for cargo in self.cargo_list:
            print (indentation+2)*' ' + 'Cargo:', cargo.value

    def get_action_list(self):
        return action0.get_cargolist_action(self.cargo_list)

    def __str__(self):
        ret = 'cargotable {\n'
        ret += ', '.join([cargo.value for cargo in self.cargo_list])
        ret += '\n}\n'
        return ret

class RailtypeTable(object):
    def __init__(self, railtype_list):
        self.railtype_list = railtype_list
        for i, railtype in enumerate(railtype_list):
            global_constants.railtype_table[railtype.value] = i

    def debug_print(self, indentation):
        print indentation*' ' + 'Railtype table'
        for railtype in self.railtype_list_list:
            print (indentation+2)*' ' + 'Railtype:', railtype.value

    def get_action_list(self):
        return action0.get_railtypelist_action(self.railtype_list)

    def __str__(self):
        ret = 'railtypetable {\n'
        ret += ', '.join([railtype.value for railtype in self.railtype_list])
        ret += '\n}\n'
        return ret

class SpriteCount(object):
    def debug_print(self, indentation):
        print indentation*' ' + 'Sprite count'

    def get_action_list(self):
        return [SpriteCountAction()]
