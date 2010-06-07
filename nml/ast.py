from nml import generic
from expression import *
from actions.action0 import *
from actions.action1 import *
from actions.real_sprite import *
from actions.action2var import *
from actions.action3 import *
from actions import action5
from actions.action7 import *
from actions.action8 import *
from actions.actionA import *
from actions.actionB import *
from actions.actionD import *
from actions.actionE import *
from actions import actionF
from actions import action12
from actions.sprite_count import SpriteCountAction
import global_constants
import unit

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

class ParameterAssignment(object):
    def __init__(self, param, value):
        self.param = param
        self.value = reduce_expr(value, [global_constants.const_table, cargo_numbers])

    def debug_print(self, indentation):
        print indentation*' ' + 'Parameter assignment'
        self.param.debug_print(indentation + 2)
        self.value.debug_print(indentation + 2)

    def get_action_list(self):
        return parse_actionD(self)

    def __str__(self):
        return 'param[%s] = %s;\n' % (str(self.param), str(self.value))

########### code blocks ###########
class GRF(object):
    def __init__(self, alist):
        self.name = None
        self.desc = None
        self.grfid = None
        for assignment in alist:
            if assignment.name == "grfid":
                if not isinstance(assignment.value, basestring):
                    raise generic.ScriptError("GRFID must be a string literal")
            elif not isinstance(assignment.value, String):
                raise generic.ScriptError("Assignments in GRF-block must be constant strings")
            if assignment.name == "name": self.name = assignment.value
            elif assignment.name == "desc": self.desc = assignment.value
            elif assignment.name == "grfid": self.grfid = assignment.value
            else: raise generic.ScriptError("Unkown item in GRF-block: " + assignment.name)

    def debug_print(self, indentation):
        print indentation*' ' + 'GRF'
        if self.grfid is not None:
            print (2+indentation)*' ' + 'grfid:', self.grfid
        if self.name is not None:
            print (2+indentation)*' ' + 'Name:'
            self.name.debug_print(indentation + 4)
        if self.desc is not None:
            print (2+indentation)*' ' + 'Description:'
            self.desc.debug_print(indentation + 4)

    def get_action_list(self):
        return [Action8(self.grfid, self.name, self.desc)]

    def __str__(self):
        ret = 'grf {\n'
        ret += '\tgrfid: "%s";\n' % str(self.grfid)
        if self.name is not None:
            ret += '\tname: %s;\n' % str(self.name)
        if self.desc is not None:
            ret += '\tdesc: %s;\n' % str(self.desc)
        ret += '}\n'
        return ret

class Conditional(object):
    def __init__(self, expr, block, else_block = None):
        self.expr = expr
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
        return parse_conditional_block(self)

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
        return parse_loop_block(self)

    def __str__(self):
        ret = 'while(%s) {\n' % self.expr
        for b in self.block:
            ret += '\t' + str(b).replace('\n', '\n\t')[0:-1]
        ret += '}\n'
        return ret

class Switch(object):
    def __init__(self, feature, var_range, name, expr, body):
        self.feature = reduce_constant(feature, [feature_ids])
        self.var_range = var_range
        self.name = name
        self.expr = expr
        self.body = body

    def debug_print(self, indentation):
        print indentation*' ' + 'Switch, Feature =',self.feature.value,', name =', self.name
        print (2+indentation)*' ' + 'Expression:'
        self.expr.debug_print(indentation + 4)
        print (2+indentation)*' ' + 'Body:'
        self.body.debug_print(indentation + 4)

    def get_action_list(self):
        return parse_varaction2(self)

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
        if isinstance(self.default, basestring):
            print (indentation+2)*' ' + 'Go to switch:', self.default
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
        elif isinstance(self.default, basestring):
            ret += '\t%s;\n' % self.default
        else:
            ret += '\t%s;\n' % str(self.default)
        return ret

class SwitchRange(object):
    def __init__(self, min, max, result):
        self.min = reduce_constant(min)
        self.max = reduce_constant(max)
        self.result = result

    def debug_print(self, indentation):
        print indentation*' ' + 'Min:'
        self.min.debug_print(indentation + 2)
        print indentation*' ' + 'Max:'
        self.max.debug_print(indentation + 2)
        print indentation*' ' + 'Result:'
        if isinstance(self.result, basestring):
            print (indentation+2)*' ' + 'Go to switch:', self.result
        elif self.result is None:
            print (indentation+2)*' ' + 'Return computed value'
        else:
            self.result.debug_print(indentation + 2)

    def __str__(self):
        ret = str(self.min)
        if self.max.value != self.min.value:
            ret += '..' + str(self.max)
        if isinstance(self.result, basestring):
            ret += ': %s;' % self.result
        elif self.result is None:
            ret += ': return;'
        else:
            ret += ': return %s;' % str(self.result)
        return ret

class DeactivateBlock(object):
    def __init__(self, grfid_list):
        self.grfid_list = [reduce_expr(grfid) for grfid in grfid_list]

    def debug_print(self, indentation):
        print indentation*' ' + 'Deactivate other newgrfs:'
        for grfid in self.grfid_list:
            grfid.debug_print(indentation + 2)

    def get_action_list(self):
        return parse_deactivate_block(self)

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
    def __init__(self, feature, body, name = None, id = None):
        global item_names
        self.feature = reduce_constant(feature, [feature_ids])
        self.body = body
        self.name = name
        if name is not None and name in item_names:
            self.id = ConstantNumeric(item_names[name])
        elif id is None: self.id = ConstantNumeric(get_free_id(self.feature.value))
        else: self.id = reduce_constant(id)
        if name is not None:
            item_names[name] = self.id.value
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
            ret += ', %s, %s' % (self.name, str(self.id))
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
        self.value = reduce_expr(value, [global_constants.const_table, cargo_numbers])
        self.unit = unit
        if unit is not None and not (isinstance(self.value, ConstantNumeric) or isinstance(self.value, ConstantFloat)):
            raise generic.ScriptError("Using a unit for a property is only allowed if the value is constant")

    def debug_print(self, indentation):
        print indentation*' ' + 'Property:', self.name
        if isinstance(self.value, basestring):
            print (indentation + 2)*' ' + 'String: ', self.value
        else:
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
        return parse_property_block(self.prop_list, item_feature, item_id)

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
        global item_feature, item_names
        wagon_id = reduce_constant(self.wagon_id, [item_names])
        return parse_graphics_block(self.graphics_block.graphics_list, self.graphics_block.default_graphics, item_feature, wagon_id, True)

class GraphicsBlock(object):
    def __init__(self, default_graphics):
        self.default_graphics = default_graphics
        self.graphics_list = []

    def append_definition(self, graphics_assignment):
        self.graphics_list.append(graphics_assignment)
        return self

    def debug_print(self, indentation):
        print indentation*' ' + 'Graphics block:'
        for graphics in self.graphics_list:
            graphics.debug_print(indentation + 2)
        print (indentation+2)*' ' + 'Default graphics:', self.default_graphics

    def get_action_list(self):
        global item_feature, item_id
        return parse_graphics_block(self.graphics_list, self.default_graphics, item_feature, item_id)

class GraphicsDefinition(object):
    def __init__(self, cargo_id, action2_id):
        self.cargo_id = cargo_id
        self.action2_id = action2_id

    def debug_print(self, indentation):
        print indentation*' ' + 'Graphics:'
        print (indentation+2)*' ' + 'Cargo:', self.cargo_id
        print (indentation+2)*' ' + 'Linked to action2:', self.action2_id

class ReplaceSprite(object):
    def __init__(self, start_id, pcx, sprite_list):
        self.start_id = reduce_constant(start_id)
        self.pcx = pcx
        self.sprite_list = sprite_list

    def debug_print(self, indentation):
        print indentation*' ' + 'Replace sprites starting at', self.start_id
        print (indentation+2)*' ' + 'Source:  ', self.pcx
        print (indentation+2)*' ' + 'Sprites:'
        for sprite in self.sprite_list:
            sprite.debug_print(indentation + 4)

    def get_action_list(self):
        return parse_actionA(self)

class ReplaceNewSprite(object):
    def __init__(self, type, pcx, offset, sprite_list):
        self.type = type
        self.pcx = pcx
        self.offset = offset
        self.sprite_list = sprite_list

    def debug_print(self, indentation):
        print indentation*' ' + 'Replace sprites for new features of type', self.type
        print (indentation+2)*' ' + 'Offset:  ', self.offset
        print (indentation+2)*' ' + 'Source:  ', self.pcx
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
        print (indentation+2)*' ' + 'Source:  ', self.pcx
        print (indentation+2)*' ' + 'Sprites:'
        for sprite in self.sprite_list:
            sprite.debug_print(indentation + 4)

    def get_action_list(self):
        return action12.parse_action12(self)

class SpriteBlock(object):
    def __init__(self, feature, spriteset_list):
        self.feature = reduce_constant(feature, [feature_ids])
        self.spriteset_list = spriteset_list

    def debug_print(self, indentation):
        print indentation*' ' + 'Sprite block, feature', hex(self.feature.value)
        for spriteset in self.spriteset_list:
            spriteset.debug_print(indentation + 2)
    def get_action_list(self):
        return parse_sprite_block(self)

class TemplateDeclaration(object):
    def __init__(self, name, param_list, sprite_list):
        self.name = name
        if name not in sprite_template_map:
            sprite_template_map[name] = self
        else:
            raise generic.ScriptError("Template named '" + name + "' is already defined")
        self.param_list = param_list
        self.sprite_list = sprite_list

    def debug_print(self, indentation):
        print indentation*' ' + 'Template declaration:', self.name
        print (indentation+2)*' ' + 'Parameters:'
        for param in self.param_list:
            print (indentation+4)*' ' + param
        print (indentation+2)*' ' + 'Sprites:'
        for sprite in self.sprite_list:
            sprite.debug_print(indentation + 4)

    def get_action_list(self):
        return []

class TemplateUsage(object):
    def __init__(self, name, param_list):
        self.name = name
        self.param_list = param_list

    def debug_print(self, indentation):
        print indentation*' ' + 'Template used:', self.name
        print (indentation+2)*' ' + 'Parameters:'
        for param in self.param_list:
            if isinstance(param, basestring):
                print (indentation+4)*' ' + 'ID:', param
            else:
                param.debug_print(indentation + 4)

class SpriteSet(object):
    def __init__(self, name, pcx, sprite_list):
        self.name = name
        self.pcx = pcx
        self.sprite_list = sprite_list

    def debug_print(self, indentation):
        print indentation*' ' + 'Sprite set:', self.name
        print (indentation+2)*' ' + 'Source:  ', self.pcx
        print (indentation+2)*' ' + 'Sprites:'
        for sprite in self.sprite_list:
            sprite.debug_print(indentation + 4)

class RealSprite(object):
    def __init__(self, param_list = None):
        self.param_list = param_list
        self.is_empty = False

    def debug_print(self, indentation):
        print indentation*' ' + 'Real sprite, parameters:'
        for param in self.param_list:
            if isinstance(param, basestring):
                print (indentation+2)*' ' + 'ID:', param
            else:
                param.debug_print(indentation + 2)

class SpriteGroup(object):
    def __init__(self, name, spriteview_list):
        self.name = name
        self.spriteview_list = spriteview_list

    def debug_print(self, indentation):
        print indentation*' ' + 'Sprite group:', self.name
        for spriteview in self.spriteview_list:
            spriteview.debug_print(indentation + 2)

class SpriteView(object):
    def __init__(self, name, spriteset_list):
        self.name = name
        self.spriteset_list = spriteset_list

    def debug_print(self, indentation):
        print indentation*' ' + 'Sprite view:', self.name
        print (indentation+2)*' ' + 'Sprite sets:'
        for spriteset in self.spriteset_list:
            print (indentation+4)*' ' + spriteset

class LayoutSpriteGroup(object):
    def __init__(self, name, layout_sprite_list):
        self.name = name
        self.layout_sprite_list = layout_sprite_list

    def debug_print(self, indentation):
        print indentation*' ' + 'Tile layout sprite group:', self.name
        for layout_sprite in self.layout_sprite_list:
            layout_sprite.debug_print(indentation + 2)

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
        self.value = reduce_expr(value, [global_constants.const_table], False)

    def debug_print(self, indentation):
        print indentation*' ' + 'Layout parameter:', self.name
        if isinstance(self.value, basestring):
            print (indentation + 2)*' ' + 'String: ', self.value
        else:
            self.value.debug_print(indentation + 2)


class TownNames(object):
    """
    town_names ast node.

    @ivar name: Name ID of the town_name.
    @type name: C{None}, C{basestring}, or L{ConstantNumeric}

    @ivar id_number: Allocated ID number for this town_name action F node.
    @type id_number: C{None} or C{int}

    @ivar style_name: Name of the translated string containing the name of the style, if any.
    @type style_name: C{None} or C{basestring}

    @ivar style_names: List translations of L{style_name}, pairs (languageID, text).
    @type style_names: C{list} of (C{int}, C{basestring})

    @ivar parts: Parts of the names.
    @type parts: C{list} of L{TownNamesPart}

    @ivar free_bit: First available bit above the bits used by this block.
    @type free_bit: C{None} if unset, else C{int}
    """
    def __init__(self, name, param_list):
        self.name = name
        self.id_number = None
        self.style_name = None
        self.style_names = []
        self.parts = []
        self.free_bit = None

        for param in param_list:
            if isinstance(param, TownNamesPart): self.parts.append(param)
            else:
                if param.key != 'styles':
                    raise generic.ScriptError("Expected 'styles' keyword.")
                if len(param.value.params) > 0:
                    raise generic.ScriptError("Parameters of the 'styles' were not expected.")
                if self.style_name is not None:
                    raise generic.ScriptError("'styles' is already defined.")
                self.style_name = param.value.name

        if len(self.parts) == 0:
            raise generic.ScriptError("Missing name parts in a town_names item.")

        # 'name' is actually a number.
        # Allocate it now, before the self.prepare_output() call (to prevent names to grab it).
        if self.name is not None and not isinstance(self.name, basestring):
            value = reduce_constant(self.name)
            if not isinstance(value, ConstantNumeric):
                raise generic.ScriptError("ID should be an integer number.")

            self.id_number = value.value
            if self.id_number < 0 or self.id_number > 0x7f:
                raise generic.ScriptError("ID must be a number between 0 and 0x7f (inclusive)")

            if self.id_number not in actionF.free_numbers:
                raise generic.ScriptError("town names ID 0x%x is already used." % self.id_number)
            actionF.free_numbers.remove(self.id_number)

    def prepare_output(self):
        global grf_strings

        # Resolve references to earlier townname actions
        blocks = set()
        for part in self.parts:
            blocks.update(part.resolve_townname_id())

        # Allocate a number for this action F.
        if self.name is None or isinstance(self.name, basestring):
            self.id_number = actionF.get_free_id()
            if isinstance(self.name, basestring):
                if self.name in actionF.named_numbers:
                    raise generic.ScriptError('Cannot define town name "%s", it is already in use' % self.name)
                actionF.named_numbers[self.name] = self.id_number # Add name to the set 'safe' names.
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
            raise generic.ScriptError("Not enough random bits for the town name generation (%d needed, 32 available)" % startbit)

        # Pull style names if needed.
        if self.style_name is not None:
            if self.style_name not in grf_strings:
                raise generic.ScriptError("Unknown string: " + self.style_name)
            self.style_names = [(transl['lang'], transl['text']) for transl in grf_strings[self.style_name]]
            self.style_names.sort()
            if len(self.style_names) == 0:
                raise generic.ScriptError('Style "%s" defined, but no translations found for it' % self.style_name)
        else: self.style_names = []


    def get_id(self):
        return self.id_number | (0x80 if len(self.style_names) > 0 else 0)

    # Style names
    def get_length_styles(self):
        if len(self.style_names) == 0: return 0
        size = 0
        for _lang, txt in self.style_names:
            size += 1 + 2 + get_string_size(txt) + 1 # Language ID, text, 0 byte
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
    """
    def __init__(self, pieces):
        self.pieces = pieces
        if len(self.pieces) == 0:
            raise generic.ScriptError("Expected names and/or town_name references in the part.")

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
            raise generic.ScriptError("Expected at least one value in a part.")
        if len(self.pieces) > 255:
            raise generic.ScriptError("Too many values in a part, found %d, maximum is 255" % len(self.pieces))
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
    def __init__(self, key, value):
        self.key = key
        self.value = value

class TownNamesEntryDefinition(object):
    """
    An entry in a part referring to a non-final town name, with a given probability.

    @ivar def_number: Name or number referring to a previous town_names node.
    @type def_number: C{basestring} or L{ConstantNumeric}

    @ivar number: Actual ID to use.
    @type number: C{None} or C{int}

    @ivar probability: Probability of picking this reference.
    @type probability: C{ConstantNumeric}
    """
    def __init__(self, def_number, probability):
        self.def_number = def_number
        self.number = None
        if not isinstance(self.def_number, basestring):
            self.def_number = reduce_constant(self.def_number)
            if not isinstance(self.def_number, ConstantNumeric):
                raise generic.ScriptError("Reference to other town name ID should be an integer number.")
            if self.def_number.value < 0 or self.def_number.value > 0x7f:
                raise generic.ScriptError("Reference number out of range (must be between 0 and 0x7f inclusive).")

        self.probability = reduce_constant(probability)
        if not isinstance(self.probability, ConstantNumeric):
            raise generic.ScriptError("Probability should be an integer number.")
        if self.probability.value < 0 or self.probability.value > 0x7f:
            raise generic.ScriptError("Probability out of range (must be between 0 and 0x7f inclusive).")

    def debug_print(self, indentation, total):
        if isinstance(self.def_number, basestring): name_text = "name '" + self.def_number + "'"
        else: name_text = "number 0x%x" % self.def_number.value
        print indentation*' ' + ('Insert town_name ID %s with probability %d/%d' % (name_text, self.probability.value, total))

    def get_length(self):
        return 2

    def resolve_townname_id(self):
        '''
        Resolve the reference number to a previous C{town_names} block.

        @return: Number of the referenced C{town_names} block.
        '''
        if isinstance(self.def_number, basestring):
            self.number = actionF.named_numbers.get(self.def_number)
            if self.number is None:
                raise generic.ScriptError('Town names name "%s" is not defined or points to a next town_names node' % self.def_number)
        else:
            self.number = self.def_number.value
            if self.number not in actionF.numbered_numbers:
                raise generic.ScriptError('Town names number "%s" is not defined or points to a next town_names node' % self.number)
        return self.number

    def write(self, file):
        file.print_bytex(self.probability.value | 0x80)
        file.print_bytex(self.number)

class TownNamesEntryText(object):
    """
    An entry in a part, a text-string with a given probability.
    """
    def __init__(self, id, text, probability):
        if id != 'text':
            raise generic.ScriptError("Expected 'text' prefix.")

        self.text = text
        if not isinstance(self.text, basestring):
            raise generic.ScriptError("Expected string literal for the name.")

        self.probability = reduce_constant(probability)
        if not isinstance(self.probability, ConstantNumeric):
            raise generic.ScriptError("Probability should be an integer number.")
        if self.probability.value < 0 or self.probability.value > 0x7f:
            raise generic.ScriptError("Probability out of range (must be between 0 and 0x7f inclusive).")

    def debug_print(self, indentation, total):
        print indentation*' ' + ('Text %s with probability %d/%d' % (self.text, self.probability.value, total))

    def get_length(self):
        return 1 + 2 + get_string_size(self.text) + 1 # probability, text, 0

    def resolve_townname_id(self):
        '''
        Resolve the reference number to a previous C{town_names} block.

        @return: C{None}, as being the block number of a referenced previous C{town_names} block.
        '''
        return None

    def write(self, file):
        file.print_bytex(self.probability.value)
        file.print_string(self.text, final_zero = True)


class Error(object):
    def __init__(self, param_list):
        self.params = []
        if not 2 <= len(param_list) <= 5:
            raise generic.ScriptError("'error' expects between 2 and 5 parameters, got " + str(len(param_list)))
        self.severity = reduce_expr(param_list[0], [error_severity])
        self.msg      = param_list[1]
        self.data     = param_list[2] if len(param_list) >= 3 else None
        self.params.append(reduce_expr(param_list[3]) if len(param_list) >= 4 else None)
        self.params.append(reduce_expr(param_list[4]) if len(param_list) >= 5 else None)

    def debug_print(self, indentation):
        print indentation*' ' + 'Error, msg = ', self.msg
        print (indentation+2)*' ' + 'Severity:'
        self.severity.debug_print(indentation + 4)
        print (indentation+2)*' ' + 'Data: ', self.data
        print (indentation+2)*' ' + 'Param1: '
        if self.params[0] is not None: self.params[0].debug_print(indentation + 4)
        print (indentation+2)*' ' + 'Param2: '
        if self.params[1] is not None: self.params[1].debug_print(indentation + 4)

    def get_action_list(self):
        return parse_error_block(self)

class CargoTable(object):
    def __init__(self, cargo_list):
        global cargo_numbers;
        self.cargo_list = cargo_list
        i = 0
        for cargo in cargo_list:
            cargo_numbers[cargo] = i
            i += 1

    def debug_print(self, indentation):
        print indentation*' ' + 'Cargo table'
        for cargo in self.cargo_list:
            print (indentation+2)*' ' + 'Cargo:', cargo

    def get_action_list(self):
        return get_cargolist_action(self.cargo_list)

    def __str__(self):
        ret = 'cargotable {\n'
        ret += ', '.join(self.cargo_list)
        ret += '\n}\n'
        return ret

class SpriteCount(object):
    def debug_print(self, indentation):
        print indentation*' ' + 'Sprite count'

    def get_action_list(self):
        return [SpriteCountAction()]
