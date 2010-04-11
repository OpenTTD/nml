import ast
from action2 import *
from generic import *

class Action2Layout(Action2):
    def __init__(self, feature, name, ground_sprite, sprite_list):
        Action2.__init__(self, feature, name)
        assert ground_sprite.type == Action2LayoutSpriteType.GROUND
        self.ground_sprite = ground_sprite
        self.sprite_list = sprite_list
        #required by grf specs
        assert len(sprite_list) != 0
    
    def write(self, file):
        Action2.write(self, file)
        print_byte(file, len(self.sprite_list))
        print_dwordx(file, self.ground_sprite.get_sprite_number())
        for sprite in self.sprite_list:
            print_dwordx(file, sprite.get_sprite_number())
            print_byte(file, sprite.get_bounding_box_param('xoffset'))
            print_byte(file, sprite.get_bounding_box_param('yoffset'))
            if sprite.type == Action2LayoutSpriteType.CHILD:
                print_bytex(file, 0x80)
            else:
                #normal building sprite
                print_byte(file, sprite.get_bounding_box_param('zoffset'))
                print_byte(file, sprite.get_bounding_box_param('xextent'))
                print_byte(file, sprite.get_bounding_box_param('yextent'))
                print_byte(file, sprite.get_bounding_box_param('zextent'))


class Action2LayoutRecolorMode:
    NONE = 0
    TRANSPARANT = 1
    RECOLOR = 2

#same keywords as in the syntax
class Action2LayoutSpriteType:
    GROUND = 'ground'
    BUILDING = 'building'
    CHILD = 'childsprite'

class Action2LayoutSprite:
    
    
    def __init__(self, type):
        self.type = type
        self._bounding_box = {
            'xoffset': {'value': 0, 'is_set': False},
            'yoffset': {'value': 0, 'is_set': False},
            'zoffset': {'value': 0, 'is_set': False},
            'xextent': {'value': 16, 'is_set': False},
            'yextent': {'value': 16, 'is_set': False}, 
            'zextent': {'value': 16, 'is_set': False}
        }
        self._sprite_number = -1
        self._recolor_type = Action2LayoutRecolorMode.NONE
        self._recolor_sprite = 0        
        self._draw_transparant = False
        self._draw_transparant_set = False

    def get_sprite_number(self):
        res = self._sprite_number
        res |= self._recolor_type << 14
        res |= self._recolor_sprite << 16
        if self._draw_transparant: res |= 1 << 30
        return res
    
    def validate(self):
        if self._sprite_number == -1:
            raise ScriptError("No sprite or ttdsprite specified. This parameter is required.")

    def set_sprite(self, ttd, number):
        if self._sprite_number == -1:
            if number >> 14 != 0:
                raise ScriptError("Sprite number too big, maximum is " + str((1 << 14) - 1))
            self._sprite_number = number
            if ttd: self._sprite_number |= 1 << 31
        else:
            raise ScriptError("Only one 'sprite'/'ttdsprite' definition allowed per ground/building/childsprite")
    
    def set_recolor_sprite(self, type, number):
        if self._recolor_type == Action2LayoutRecolorMode.NONE:
            if number >> 14 != 0:
                raise ScriptError("Recolor sprite number too big, maximum is " + str((1 << 14) - 1))
            self._recolor_type = type
            self._recolor_sprite = number
        else:
            raise ScriptError("Only one recolor sprite may be set per per ground/building/childsprite")
    
    def set_draw_transparant(self, value):
        #bit may not be set for ground sprites, according to grf specs
        if self.type == Action2LayoutSpriteType.GROUND:
            raise ScriptError("Ground sprites cannot be drawn transparantly")
        if self._draw_transparant_set:
            raise ScriptError("Transparancy may be set only once per sprite")
        self._draw_transparant = value

    def is_bounding_box_param(self, name):
        return name in self._bounding_box
    
    def set_bounding_box_param(self, name, value):
        assert name in self._bounding_box
        if self.type == Action2LayoutSpriteType.GROUND:
            raise ScriptError(name + " can not be set for ground sprites")
        if self.type == Action2LayoutSpriteType.CHILD and name != 'xoffset' and name != 'yoffset':
            raise ScriptError(name + " can not be set for child sprites")
        
        if self._bounding_box[name]['is_set']:
            raise ScriptError(name + " may be set only once per sprite")
        
        if value > 127 or value < -128:
            raise ScriptError(name + " has to be in range -128..127")
        
        if name == 'zoffset' and value != 0:
            raise ScriptError("zoffset should always be 0")
                
        self._bounding_box[name]['value'] = value
        self._bounding_box[name]['is_set'] = True

    
    def get_bounding_box_param(self, name):
        assert name in self._bounding_box
        return self._bounding_box[name]['value']

def set_sprite_property(sprite, name, value, spritesets):

    if name == 'sprite':
        if not isinstance(value, str):
            raise ScriptError("Value of 'sprite' should be a spritset identifier")
        if value not in spritesets:
            raise ScriptError("Unknown sprite set: " + value)
        sprite.set_sprite(False, spritesets[value])
    
    elif name == 'ttdsprite':
        if not isinstance(value, ast.ConstantNumeric):
            raise ScriptError("Value of 'ttdsprite' should be a compile-time constant")
        sprite.set_sprite(True, value.value)
    
    elif name == 'recolor':
        if isinstance(value, str):
            if value == 'TRANSPARANT':
                sprite.set_recolor_sprite(Action2LayoutRecolorMode.TRANSPARANT, 0)
            else:
                raise ScriptError("Value of 'recolor' should be either 'TRANSPARANT' or a compile-time constant sprite number, encountered " + value )
        elif isinstance(value, ast.ConstantNumeric):
            sprite.set_recolor_sprite(Action2LayoutRecolorMode.RECOLOR, value.value)
        else:
            raise ScriptError("Value of 'recolor' should be either 'TRANSPARANT' or a compile-time constant sprite number")
    
    elif name == 'always_draw':
        if isinstance(value, ast.ConstantNumeric):
            sprite.set_draw_transparant(value.value != 0)
        else:
            raise ScriptError("Value of 'always_draw' should be a compile-time constant")
    
    else:
        if sprite.is_bounding_box_param(name):
            if isinstance(value, ast.ConstantNumeric):
                sprite.set_bounding_box_param(name, value.value)
            else:
                raise ScriptError("Value of '" + name + "' should be a compile-time constant")
        else:
            raise ScriptError("Unknown sprite layout parameter: " + name)

def get_layout_action2s(spritegroup, feature, spritesets):
    ground_sprite = None
    building_sprites = []
    
    for layout_sprite in spritegroup.layout_sprite_list:
        sprite = Action2LayoutSprite(layout_sprite.type)
        for param in layout_sprite.param_list:
            set_sprite_property(sprite, param.name, param.value, spritesets)
        sprite.validate()
        if sprite.type == Action2LayoutSpriteType.GROUND:
            if ground_sprite is not None:
                raise ScriptError("Sprite group can have no more than one ground sprite")
            ground_sprite = sprite
        else:
            building_sprites.append(sprite)
    
    if ground_sprite is None:
        raise ScriptError("Sprite group requires exactly one ground sprite")
    if len(building_sprites) == 0:
        raise ScriptError("At least one non-ground sprite must be specified per sprite group")    
        
    return [Action2Layout(feature, spritegroup.name, ground_sprite, building_sprites)]