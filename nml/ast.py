from expression import *
from actions.action0 import *
from actions.action1 import *
from actions.real_sprite import *
from actions.action2var import *
from actions.action3 import *
from actions.action7 import *
from actions.action8 import *
from actions.actionA import *
from actions.actionB import *
from actions.actionD import *
from actions.actionE import *
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

class ParameterAssignment:
    def __init__(self, param, value):
        self.param = param
        self.value = reduce_expr(value, [global_constants.const_table])
    
    def debug_print(self, indentation):
        print indentation*' ' + 'Parameter assignment'
        self.param.debug_print(indentation + 2)
        self.value.debug_print(indentation + 2)
    
    def get_action_list(self):
        return parse_actionD(self)

########### code blocks ###########
class GRF:
    def __init__(self, alist):
        self.name = None
        self.desc = None
        self.grfid = None
        for assignment in alist:
            if assignment.name == "grfid":
                if not isinstance(assignment.value, str):
                    raise ScriptError("GRFID must be a string literal")
            elif not isinstance(assignment.value, String):
                raise ScriptError("Assignments in GRF-block must be constant strings")
            if assignment.name == "name": self.name = assignment.value
            elif assignment.name == "desc": self.desc = assignment.value
            elif assignment.name == "grfid": self.grfid = assignment.value
            else: raise ScriptError("Unkown item in GRF-block: " + assignment.name)
    
    def debug_print(self, indentation):
        print indentation*' ' + 'GRF'
        if self.grfid != None:
            print (2+indentation)*' ' + 'grfid:', self.grfid
        if self.name != None:
            print (2+indentation)*' ' + 'Name:'
            self.name.debug_print(indentation + 4)
        if self.desc != None:
            print (2+indentation)*' ' + 'Description:'
            self.desc.debug_print(indentation + 4)
    
    def get_action_list(self):
        return [Action8(self.grfid, self.name, self.desc)]

class Conditional:
    def __init__(self, expr, block, else_block = None):
        self.expr = expr
        self.block = block
        self.else_block = else_block
    
    def debug_print(self, indentation):
        print indentation*' ' + 'Conditional'
        if self.expr != None:
            print (2+indentation)*' ' + 'Expression:'
            self.expr.debug_print(indentation + 4)
        print (2+indentation)*' ' + 'Block:'
        print_script(self.block, indentation + 4)
        if self.else_block != None:
            print (indentation)*' ' + 'Else block:'
            self.else_block.debug_print(indentation)
    
    def get_action_list(self):
        return parse_conditional_block(self)

class Loop:
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

class Switch:
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

class SwitchBody:
    def __init__(self, default):
        self.default = default
        self.ranges = []
    
    def add_range(self, switch_range):
        self.ranges.append(switch_range)
        return self
    
    def debug_print(self, indentation):
        for r in self.ranges:
            r.debug_print(indentation)
        print indentation*' ' + 'Default:'
        if isinstance(self.default, str):
            print (indentation+2)*' ' + 'Go to switch:', self.default
        else:
            self.default.debug_print(indentation + 2)

class SwitchRange:
    def __init__(self, min, max, result):
        self.min = min
        self.max = max
        self.result = result
    
    def debug_print(self, indentation):
        print indentation*' ' + 'Min:'
        self.min.debug_print(indentation + 2)
        print indentation*' ' + 'Max:'
        self.max.debug_print(indentation + 2)
        print indentation*' ' + 'Result:'
        if isinstance(self.result, str):
            print (indentation+2)*' ' + 'Go to switch:', self.result
        else:
            self.result.debug_print(indentation + 2)

class DeactivateBlock:
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
            while block != None:
                validate_item_block(block.block)
                block = block.else_block
            continue
        if isinstance(block, Loop):
            validate_item_block(block.body)
            continue
        raise ScriptError("Invalid block type inside 'Item'-block")

item_feature = None
item_id = None

class Item:
    def __init__(self, feature, body, id = None):
        self.feature = reduce_constant(feature, [feature_ids])
        self.body = body
        self.id = id
        validate_item_block(body)
    
    def debug_print(self, indentation):
        print indentation*' ' + 'Item, feature', hex(self.feature.value)
        for b in self.body: b.debug_print(indentation + 2)
    
    def get_action_list(self):
        global item_feature, item_id
        if self.id != None:
            item_id = self.id
        else:
            item_id = ConstantNumeric(get_free_id(self.feature.value))
        item_feature = self.feature.value
        action_list = []
        for b in self.body:
            action_list.extend(b.get_action_list())
        return action_list

class Unit:
    def __init__(self, name):
        assert name in unit.units
        self.type = unit.units[name]['type']
        self.convert = unit.units[name]['convert']

class Property:
    def __init__(self, name, value, unit):
        self.name = name
        self.value = reduce_expr(value, [global_constants.const_table])
        self.unit = unit
        if unit != None and not isinstance(self.value, ConstantNumeric):
            raise ScriptError("Using a unit for a property is only allowed if the value is constant")
    
    def debug_print(self, indentation):
        print indentation*' ' + 'Property:', self.name
        if isinstance(self.value, str):
            print (indentation + 2)*' ' + 'String: ', self.value
        else:
            self.value.debug_print(indentation + 2)

class PropertyBlock:
    def __init__(self, prop_list):
        self.prop_list = prop_list
    
    def debug_print(self, indentation):
        print indentation*' ' + 'Property block:'
        for prop in self.prop_list:
            prop.debug_print(indentation + 2)
    
    def get_action_list(self):
        global item_feature, item_id
        return parse_property_block(self.prop_list, item_feature, item_id)

class LiveryOverride:
    def __init__(self, wagon_id, graphics_block):
        self.graphics_block = graphics_block
        self.wagon_id = reduce_constant(wagon_id)
    
    def debug_print(self, indentation):
        print indentation*' ' + 'Liverry override, wagon id:', self.wagon_id
        for graphics in self.graphics_list:
            graphics.debug_print(indentation + 2)
    
    def get_action_list(self):
        global item_feature
        return parse_graphics_block(self.graphics_block.graphics_list, self.graphics_block.default_graphics, item_feature, self.wagon_id, True)

class GraphicsBlock:
    def __init__(self, default_graphics):
        self.default_graphics = default_graphics
        self.graphics_list = []
    
    def append_definition(self, graphics_assignment):
        self.graphics_list.append(graphics_assignment)
    
    def debug_print(self, indentation):
        print indentation*' ' + 'Graphics block:'
        for graphics in self.graphics_list:
            graphics.debug_print(indentation + 2)
    
    def get_action_list(self):
        global item_feature, item_id
        return parse_graphics_block(self.graphics_list, self.default_graphics, item_feature, item_id)

class GraphicsDefinition:
    def __init__(self, cargo_id, action2_id):
        self.cargo_id = cargo_id
        self.action2_id = action2_id
    
    def debug_print(self, indentation):
        print indentation*' ' + 'Graphics:'
        print (indentation+2)*' ' + 'Cargo:', self.cargo_id
        print (indentation+2)*' ' + 'Linked to action2:', self.action2_id

class ReplaceSprite:
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

class SpriteBlock:
    def __init__(self, feature, spriteset_list):
        self.feature = reduce_constant(feature, [feature_ids])
        self.spriteset_list = spriteset_list
    
    def debug_print(self, indentation):
        print indentation*' ' + 'Sprite block, feature', hex(self.feature.value)
        for spriteset in self.spriteset_list:
            spriteset.debug_print(indentation + 2)
    def get_action_list(self):
        return parse_sprite_block(self)

class SpriteSet:
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

class EmptyRealSprite:
    def debug_print(self, indentation):
        print indentation*' ' + 'Empty real sprite'

class RealSprite:
    def __init__(self, param_list):
        if not 6 <= len(param_list) <= 7:
            raise ScriptError("Invalid number of arguments for real sprite. Expected 6 or 7.")
        try:
            self.xpos  = reduce_constant(param_list[0])
            self.ypos  = reduce_constant(param_list[1])
            self.xsize = reduce_constant(param_list[2])
            self.ysize = reduce_constant(param_list[3])
            self.xrel  = reduce_constant(param_list[4])
            self.yrel  = reduce_constant(param_list[5])
            
            check_range(self.xpos.value,  0, 0x7fffFFFF,   "Real sprite paramater 'xpos'")
            check_range(self.ypos.value,  0, 0x7fffFFFF,   "Real sprite paramater 'ypos'")
            check_range(self.xsize.value, 1, 0xFFFF,       "Real sprite paramater 'xsize'")
            check_range(self.ysize.value, 1, 0xFF,         "Real sprite paramater 'ysize'")
            check_range(self.xrel.value, -0x8000, 0x7fff,  "Real sprite paramater 'xrel'")
            check_range(self.yrel.value, -0x8000, 0x7fff,  "Real sprite paramater 'yrel'")
            
            if len(param_list) == 7:
                self.compression = reduce_constant(param_list[6], [real_sprite_compression_flags])
                self.compression.value |= 0x01
            else:
                self.compression = ConstantNumeric(0x01)
            # only bits 0, 1, 3, and 6 can be set
            if (self.compression.value & ~0x4B) != 0:
                raise ScriptError("Real sprite compression is invalid; can only have bit 0, 1, 3 and/or 6 set, encountered " + str(self.compression.value))
        except ConstError:
            raise ScriptError("Real sprite parameters should be compile-time constants.")
    
    def debug_print(self, indentation):
        print indentation*' ' + 'Real sprite'
        print (indentation+2)*' ' + 'position: (', self.xpos.value,  ',', self.ypos.value,  ')'
        print (indentation+2)*' ' + 'size:     (', self.xsize.value, ',', self.ysize.value, ')'
        print (indentation+2)*' ' + 'offset:   (', self.xrel.value,  ',', self.yrel.value,  ')'
        print (indentation+2)*' ' + 'compression: ', self.compression.value

class SpriteGroup:
    def __init__(self, name, spriteview_list):
        self.name = name
        self.spriteview_list = spriteview_list
    
    def debug_print(self, indentation):
        print indentation*' ' + 'Sprite group:', self.name
        for spriteview in self.spriteview_list:
            spriteview.debug_print(indentation + 2)

class SpriteView:
    def __init__(self, name, spriteset_list):
        self.name = name
        self.spriteset_list = spriteset_list
    
    def debug_print(self, indentation):
        print indentation*' ' + 'Sprite view:', self.name
        print (indentation+2)*' ' + 'Sprite sets:'
        for spriteset in self.spriteset_list:
            print (indentation+4)*' ' + spriteset

class LayoutSpriteGroup:
    def __init__(self, name, layout_sprite_list):
        self.name = name
        self.layout_sprite_list = layout_sprite_list
    
    def debug_print(self, indentation):
        print indentation*' ' + 'Tile layout sprite group:', self.name
        for layout_sprite in self.layout_sprite_list:
            layout_sprite.debug_print(indentation + 2)

class LayoutSprite:
    def __init__(self, type, param_list):
        self.type = type
        self.param_list = param_list
    
    def debug_print(self, indentation):
        print indentation*' ' + 'Tile layout sprite of type:', self.type
        for layout_param in self.param_list:
            layout_param.debug_print(indentation + 2)

class LayoutParam:
    def __init__(self, name, value):
        self.name = name
        self.value = value
    
    def debug_print(self, indentation):
        print indentation*' ' + 'Layout parameter:', self.name
        if isinstance(self.value, str):
            print (indentation + 2)*' ' + 'String: ', self.value
        else:
            self.value.debug_print(indentation + 2)

class Error:
    def __init__(self, param_list):
        self.params = []
        if not 2 <= len(param_list) <= 5:
            raise ScriptError("'error' expects between 2 and 5 parameters, got " + str(len(param_list)))
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

class CargoTable:
    def __init__(self, cargo_list):
        self.cargo_list = cargo_list
    
    def debug_print(self, indentation):
        print indentation*' ' + 'Cargo table'
        for cargo in self.cargo_list:
            print (indentation+2)*' ' + 'Cargo:', cargo
    
    def get_action_list(self):
        return get_cargolist_action(self.cargo_list)

class SpriteCount:
    def debug_print(self, indentation):
        print indentation*' ' + 'Sprite count'
    
    def get_action_list(self):
        return [SpriteCountAction()]
