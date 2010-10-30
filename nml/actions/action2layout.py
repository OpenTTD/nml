from nml import generic, expression
from nml.actions import action2

class Action2Layout(action2.Action2):
    def __init__(self, feature, name, ground_sprite, sprite_list):
        action2.Action2.__init__(self, feature, name)
        assert ground_sprite.type == Action2LayoutSpriteType.GROUND
        self.ground_sprite = ground_sprite
        self.sprite_list = sprite_list

    def write(self, file):
        size = 5
        for sprite in self.sprite_list:
            if sprite.type == Action2LayoutSpriteType.CHILDSPRITE:
                size += 7
            else:
                size += 10
        if len(self.sprite_list) == 0:
            size += 9

        action2.Action2.write_sprite_start(self, file, size)
        file.print_byte(len(self.sprite_list))
        file.print_dwordx(self.ground_sprite.get_sprite_number())
        file.newline()
        if len(self.sprite_list) == 0:
            file.print_dwordx(0) #sprite number 0 == no sprite
            for i in range(0, 5):
                file.print_byte(0) #empty bounding box. Note that number of zeros is 5, not 6
        else:
            for sprite in self.sprite_list:
                file.print_dwordx(sprite.get_sprite_number())
                file.print_byte(sprite.get_param('xoffset'))
                file.print_byte(sprite.get_param('yoffset'))
                if sprite.type == Action2LayoutSpriteType.CHILDSPRITE:
                    file.print_bytex(0x80)
                else:
                    #normal building sprite
                    file.print_byte(sprite.get_param('zoffset'))
                    file.print_byte(sprite.get_param('xextent'))
                    file.print_byte(sprite.get_param('yextent'))
                    file.print_byte(sprite.get_param('zextent'))
                file.newline()
        file.end_sprite()


#same keywords as in the syntax
class Action2LayoutSpriteType(object):
    GROUND      = 'ground'
    BUILDING    = 'building'
    CHILDSPRITE = 'childsprite'

class Action2LayoutSprite(object):
    def __init__(self, type, pos):
        self.type = type
        self.pos = pos
        self.params = {
            'sprite'      : {'value': 0,  'validator': self._validate_sprite},
            'ttdsprite'   : {'value': 0,  'validator': self._validate_ttdsprite},
            'recolor'     : {'value': 0,  'validator': self._validate_recolor},
            'always_draw' : {'value': 0,  'validator': self._validate_always_draw},
            'xoffset'     : {'value': 0,  'validator': self._validate_bounding_box},
            'yoffset'     : {'value': 0,  'validator': self._validate_bounding_box},
            'zoffset'     : {'value': 0,  'validator': self._validate_bounding_box},
            'xextent'     : {'value': 16, 'validator': self._validate_bounding_box},
            'yextent'     : {'value': 16, 'validator': self._validate_bounding_box},
            'zextent'     : {'value': 16, 'validator': self._validate_bounding_box}
        }
        for i in self.params:
            self.params[i]['is_set'] = False

    def get_sprite_number(self):
        assert not (self.is_set('sprite') and self.is_set('ttdsprite'))
        if not (self.is_set('sprite') or self.is_set('ttdsprite')):
            raise generic.ScriptError("Either 'sprite' or 'ttdsprite' must be set for this layout sprite", self.pos)
        sprite_num = self.get_param('ttdsprite') if self.is_set('ttdsprite') else self.get_param('sprite') | (1 << 31)
        recolor = self.get_param('recolor')
        if recolor == -1:
            sprite_num |= 1 << 14
        elif recolor != 0:
            sprite_num |= 1 << 15
            sprite_num |= recolor << 16
        if self.get_param('always_draw'):
            sprite_num |= 1 << 30
        return sprite_num

    def get_param(self, name):
        assert name in self.params
        return self.params[name]['value']

    def is_set(self, name):
        assert name in self.params
        return self.params[name]['is_set']

    def set_param(self, name, value):
        assert isinstance(name, expression.Identifier)
        assert isinstance(value, expression.Expression)
        name = name.value

        if not name in self.params:
            raise generic.ScriptError("Unknown sprite parameter '%s'" % name, value.pos)
        if self.is_set(name):
            raise generic.ScriptError("Sprite parameter '%s' can be set only once per sprite." % name, value.pos)

        self.params[name]['value'] = self.params[name]['validator'](name, value)
        self.params[name]['is_set'] = True

    def _validate_sprite(self, name, value):
        if not isinstance(value, expression.Identifier):
            raise generic.ScriptError("Value of 'sprite' should be a spriteset identifier", value.pos)
        spriteset = action2.resolve_spritegroup(value, None, False, True)
        num = spriteset.action1_num
        generic.check_range(num, 0, (1 << 14) - 1, "sprite", value.pos)
        if self.is_set('ttdsprite'):
            raise generic.ScriptError("Only one 'sprite'/'ttdsprite' definition allowed per ground/building/childsprite", value.pos)
        return num

    def _validate_ttdsprite(self, name, value):
        num = value.reduce_constant().value
        generic.check_range(num, 0, (1 << 14) - 1, "ttdsprite", value.pos)
        if self.is_set('sprite'):
            raise generic.ScriptError("Only one 'sprite'/'ttdsprite' definition allowed per ground/building/childsprite", value.pos)
        return num

    def _validate_recolor(self, name, value):
        num = value.reduce_constant().value
        generic.check_range(num, -1, (1 << 14) - 1, "recolor", value.pos)
        return num

    def _validate_always_draw(self, name, value):
        num = value.reduce_constant().value
        if num not in (0, 1):
            raise generic.ScriptError("Value of 'always_draw' should be 0 or 1", value.pos)
        #bit has no effect for ground sprites but should be left empty, so ignore it
        return num if self.type != Action2LayoutSpriteType.GROUND else 0

    def _validate_bounding_box(self, name, value):
        val = value.reduce_constant().value

        if self.type == Action2LayoutSpriteType.GROUND:
            raise generic.ScriptError(name + " can not be set for ground sprites", value.pos)
        elif self.type == Action2LayoutSpriteType.CHILDSPRITE:
            if name not in ('xoffset', 'yoffset'):
                raise generic.ScriptError(name + " can not be set for child sprites", value.pos)
            generic.check_range(val, 0, 255, name, value.pos)
        else:
            assert self.type == Action2LayoutSpriteType.BUILDING
            if name == 'zoffset':
                if val != 0:
                    raise generic.ScriptError("Value of 'zoffset' should always be 0", value.pos)
            elif name in ('xoffset', 'yoffset'):
                generic.check_range(val, -128, 127, name, value.pos)
            else:
                generic.check_range(val, 0, 255, name, value.pos)
        return val

layout_action2_features = [0x07, 0x09, 0x0F, 0x11] #houses, industry tiles, objects and airport tiles

def get_layout_action2s(spritegroup, feature):
    global layout_action2_features
    ground_sprite = None
    building_sprites = []

    if feature not in layout_action2_features:
        raise generic.ScriptError("Sprite groups that define tile layouts are not supported for this feature: 0x" + generic.to_hex(feature, 2))

    for layout_sprite in spritegroup.layout_sprite_list:
        sprite = Action2LayoutSprite(layout_sprite.type, layout_sprite.pos)
        for param in layout_sprite.param_list:
            sprite.set_param(param.name, param.value)
        if sprite.type == Action2LayoutSpriteType.GROUND:
            if ground_sprite is not None:
                raise generic.ScriptError("Sprite group can have no more than one ground sprite", spritegroup.pos)
            ground_sprite = sprite
        else:
            building_sprites.append(sprite)

    if ground_sprite is None:
        if len(building_sprites) == 0:
            #no sprites defined at all, that's not very much.
            raise generic.ScriptError("Sprite group requires at least one sprite", spritegroup.pos)
        #set to 0 for no ground sprite
        ground_sprite = Action2LayoutSprite(Action2LayoutSpriteType.GROUND)
        set_sprite_property(ground_sprite, 'ttdsprite', expression.ConstantNumeric(0))

    return [Action2Layout(feature, spritegroup.name.value, ground_sprite, building_sprites)]
