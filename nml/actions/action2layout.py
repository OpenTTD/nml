from nml import generic, expression
from nml.actions import action2

class Action2Layout(action2.Action2):
    def __init__(self, feature, name, ground_sprite, sprite_list):
        action2.Action2.__init__(self, feature, name)
        assert ground_sprite.type == Action2LayoutSpriteType.GROUND
        self.ground_sprite = ground_sprite
        self.sprite_list = sprite_list
        #required by grf specs
        assert len(sprite_list) != 0

    def write(self, file):
        size = 5
        for sprite in self.sprite_list:
            if sprite.type == Action2LayoutSpriteType.CHILD:
                size += 7
            else:
                size += 10

        action2.Action2.write(self, file, size)
        file.print_byte(len(self.sprite_list))
        file.print_dwordx(self.ground_sprite.get_sprite_number())
        file.newline()
        for sprite in self.sprite_list:
            file.print_dwordx(sprite.get_sprite_number())
            file.print_byte(sprite.get_bounding_box_param('xoffset'))
            file.print_byte(sprite.get_bounding_box_param('yoffset'))
            if sprite.type == Action2LayoutSpriteType.CHILD:
                file.print_bytex(0x80)
            else:
                #normal building sprite
                file.print_byte(sprite.get_bounding_box_param('zoffset'))
                file.print_byte(sprite.get_bounding_box_param('xextent'))
                file.print_byte(sprite.get_bounding_box_param('yextent'))
                file.print_byte(sprite.get_bounding_box_param('zextent'))
            file.newline()
        file.newline()

class Action2LayoutRecolorMode(object):
    NONE = 0
    TRANSPARANT = 1
    RECOLOR = 2

#same keywords as in the syntax
class Action2LayoutSpriteType(object):
    GROUND = 'ground'
    BUILDING = 'building'
    CHILD = 'childsprite'

class Action2LayoutSprite(object):


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
            raise generic.ScriptError("No sprite or ttdsprite specified. This parameter is required.")

    def set_sprite(self, ttd, number):
        if self._sprite_number == -1:
            if number >> 14 != 0:
                raise generic.ScriptError("Sprite number too big, maximum is " + str((1 << 14) - 1))
            self._sprite_number = number
            if not ttd: self._sprite_number |= 1 << 31
        else:
            raise generic.ScriptError("Only one 'sprite'/'ttdsprite' definition allowed per ground/building/childsprite")

    def set_recolor_sprite(self, type, number):
        if self._recolor_type == Action2LayoutRecolorMode.NONE:
            if number >> 14 != 0:
                raise generic.ScriptError("Recolor sprite number too big, maximum is " + str((1 << 14) - 1))
            self._recolor_type = type
            self._recolor_sprite = number
        else:
            raise generic.ScriptError("Only one recolor sprite may be set per per ground/building/childsprite")

    def set_draw_transparant(self, value):
        if self._draw_transparant_set:
            raise generic.ScriptError("'always_draw' may be set only once per sprite")
        self._draw_transparant_set = True
        #bit has no effect for ground sprites but should be left empty, so ignore it
        if self.type != Action2LayoutSpriteType.GROUND:
            self._draw_transparant = value


    def is_bounding_box_param(self, name):
        return name in self._bounding_box

    def set_bounding_box_param(self, name, value):
        assert name in self._bounding_box
        if self.type == Action2LayoutSpriteType.GROUND:
            raise generic.ScriptError(name + " can not be set for ground sprites")
        if name == 'xoffset' or name == 'yoffset':
            if value > 127 or value < -128:
                raise generic.ScriptError(name + " has to be in range -128..127, encountered " + str(value))
        else:
            if self.type == Action2LayoutSpriteType.CHILD:
                raise generic.ScriptError(name + " can not be set for child sprites")
            if value < 0 or value > 255:
                raise generic.ScriptError(name + " has to be in range 0..255, encountered " + str(value))

        if self._bounding_box[name]['is_set']:
            raise generic.ScriptError(name + " may be set only once per sprite")


        if name == 'zoffset' and value != 0:
            raise generic.ScriptError("zoffset should always be 0, encountered " + str(value))

        self._bounding_box[name]['value'] = value
        self._bounding_box[name]['is_set'] = True


    def get_bounding_box_param(self, name):
        assert name in self._bounding_box
        return self._bounding_box[name]['value']

def set_sprite_property(sprite, name, value, spritesets):

    if name == 'sprite':
        if not isinstance(value, expression.Identifier):
            raise generic.ScriptError("Value of 'sprite' should be a spriteset identifier")
        if value.value not in spritesets:
            raise generic.ScriptError("Unknown sprite set: " + str(value))
        sprite.set_sprite(False, spritesets[value.value])

    elif name == 'ttdsprite':
        if not isinstance(value, expression.ConstantNumeric):
            raise generic.ScriptError("Value of 'ttdsprite' should be a compile-time constant")
        sprite.set_sprite(True, value.value)

    elif name == 'recolor':
        if isinstance(value, expression.Identifier):
            if value.value == 'TRANSPARANT':
                sprite.set_recolor_sprite(Action2LayoutRecolorMode.TRANSPARANT, 0)
            else:
                raise generic.ScriptError("Value of 'recolor' should be either 'TRANSPARANT' or a compile-time constant sprite number, encountered " + str(value))
        elif isinstance(value, expression.ConstantNumeric):
            sprite.set_recolor_sprite(Action2LayoutRecolorMode.RECOLOR, value.value)
        else:
            raise generic.ScriptError("Value of 'recolor' should be either 'TRANSPARANT' or a compile-time constant sprite number")

    elif name == 'always_draw':
        if isinstance(value, expression.ConstantNumeric):
            sprite.set_draw_transparant(value.value != 0)
        else:
            raise generic.ScriptError("Value of 'always_draw' should be a compile-time constant")

    else:
        if sprite.is_bounding_box_param(name):
            if isinstance(value, expression.ConstantNumeric):
                sprite.set_bounding_box_param(name, value.value)
            else:
                raise generic.ScriptError("Value of '" + name + "' should be a compile-time constant")
        else:
            raise generic.ScriptError("Unknown sprite layout parameter: " + name)

layout_action2_features = [0x07, 0x09, 0x11] #houses, industry and airport tiles

def get_layout_action2s(spritegroup, feature, spritesets):
    global layout_action2_features
    ground_sprite = None
    building_sprites = []

    if feature not in layout_action2_features:
        raise generic.ScriptError("Sprite groups that define tile layouts are not supported for this feature: 0x" + generic.to_hex(feature, 2))

    for layout_sprite in spritegroup.layout_sprite_list:
        sprite = Action2LayoutSprite(layout_sprite.type)
        for param in layout_sprite.param_list:
            set_sprite_property(sprite, param.name.value, param.value, spritesets)
        sprite.validate()
        if sprite.type == Action2LayoutSpriteType.GROUND:
            if ground_sprite is not None:
                raise generic.ScriptError("Sprite group can have no more than one ground sprite")
            ground_sprite = sprite
        else:
            building_sprites.append(sprite)

    if ground_sprite is None:
        raise generic.ScriptError("Sprite group requires exactly one ground sprite")
    if len(building_sprites) == 0:
        raise generic.ScriptError("At least one non-ground sprite must be specified per sprite group")

    return [Action2Layout(feature, spritegroup.name.value, ground_sprite, building_sprites)]
