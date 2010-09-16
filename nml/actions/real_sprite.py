from nml import generic, expression

class RealSprite(object):
    def __init__(self, param_list = None):
        self.param_list = param_list
        self.is_empty = False

    def debug_print(self, indentation):
        print indentation*' ' + 'Real sprite, parameters:'
        for param in self.param_list:
            param.debug_print(indentation + 2)

class RealSpriteAction(object):
    def __init__(self, sprite):
        self.sprite = sprite
        self.last = False

    def prepare_output(self):
        pass

    def write(self, file):
        if self.sprite.is_empty:
            file.print_empty_realsprite()
        else:
            file.print_sprite(self.sprite)
        if self.last: file.newline()

    def skip_action7(self):
        return True

    def skip_action9(self):
        return True

    def skip_needed(self):
        return True

class TemplateUsage(object):
    def __init__(self, name, param_list, pos):
        self.name = name
        self.param_list = param_list
        self.pos = pos

    def debug_print(self, indentation):
        print indentation*' ' + 'Template used:', self.name.value
        print (indentation+2)*' ' + 'Parameters:'
        for param in self.param_list:
            param.debug_print(indentation + 4)

    def expand(self, default_file, parameters = {}):
        real_sprite_list = []
        if self.name.value not in sprite_template_map:
            raise generic.ScriptError("Encountered unknown template identifier: " + self.name.value, self.name.pos)
        template = sprite_template_map[self.name.value]
        if len(self.param_list) != len(template.param_list):
            raise generic.ScriptError("Incorrect number of template arguments. Expected " + str(len(template.param_list)) + ", got " + str(len(self.param_list)), self.pos)
        param_dict = {}
        for i, param in enumerate(self.param_list):
            param = param.reduce([real_sprite_compression_flags, parameters])
            if not isinstance(param, (expression.ConstantNumeric, expression.StringLiteral)):
                raise generic.ScriptError("Template parameters should be compile-time constants", param.pos)
            param_dict[template.param_list[i].value] = param.value

        real_sprite_list.extend(parse_sprite_list(template.sprite_list, default_file, param_dict, False))
        return real_sprite_list

real_sprite_compression_flags = {
    'NORMAL'       : 0x00,
    'TILE'         : 0x08,
    'UNCOMPRESSED' : 0x00,
    'COMPRESSED'   : 0x02,
    'CROP'         : 0x00,
    'NOCROP'       : 0x40,
}


def parse_real_sprite(sprite, default_file, id_dict):
    if len(sprite.param_list) == 0:
        sprite.is_empty = True
        return RealSpriteAction(sprite)
    elif not 6 <= len(sprite.param_list) <= 8:
        raise generic.ScriptError("Invalid number of arguments for real sprite. Expected 6 to 8.")
    try:
        # create new sprite struct, needed for template expansion
        new_sprite = RealSprite()

        new_sprite.xpos  = sprite.param_list[0].reduce_constant([id_dict])
        new_sprite.ypos  = sprite.param_list[1].reduce_constant([id_dict])
        new_sprite.xsize = sprite.param_list[2].reduce_constant([id_dict])
        new_sprite.ysize = sprite.param_list[3].reduce_constant([id_dict])
        new_sprite.xrel  = sprite.param_list[4].reduce_constant([id_dict])
        new_sprite.yrel  = sprite.param_list[5].reduce_constant([id_dict])

        generic.check_range(new_sprite.xpos.value,  0, 0x7fffFFFF,   "Real sprite paramater 'xpos'", new_sprite.xpos.pos)
        generic.check_range(new_sprite.ypos.value,  0, 0x7fffFFFF,   "Real sprite paramater 'ypos'", new_sprite.ypos.pos)
        generic.check_range(new_sprite.xsize.value, 1, 0xFFFF,       "Real sprite paramater 'xsize'", new_sprite.xsize.pos)
        generic.check_range(new_sprite.ysize.value, 1, 0xFF,         "Real sprite paramater 'ysize'", new_sprite.ysize.pos)
        generic.check_range(new_sprite.xrel.value, -0x8000, 0x7fff,  "Real sprite paramater 'xrel'", new_sprite.xrel.pos)
        generic.check_range(new_sprite.yrel.value, -0x8000, 0x7fff,  "Real sprite paramater 'yrel'", new_sprite.yrel.pos)

        if len(sprite.param_list) >= 7:
            new_sprite.compression = sprite.param_list[6].reduce_constant([real_sprite_compression_flags, id_dict])
            new_sprite.compression.value |= 0x01
        else:
            new_sprite.compression = expression.ConstantNumeric(0x01)
        # only bits 0, 1, 3, and 6 can be set
        if (new_sprite.compression.value & ~0x4B) != 0:
            raise generic.ScriptError("Real sprite compression is invalid; can only have bit 0, 1, 3 and/or 6 set, encountered " + str(new_sprite.compression.value), new_sprite.compression.pos)

        if len(sprite.param_list) >= 8:
            new_sprite.file = sprite.param_list[7].reduce([id_dict])
            if not isinstance(new_sprite.file, expression.StringLiteral):
                raise generic.ScriptError("Real sprite parameter 8 'file' should be a string literal", new_sprite.file.pos)
        elif default_file is not None:
            new_sprite.file = default_file
        else:
            raise generic.ScriptError("No image file specified for real sprite")
    except generic.ConstError:
        raise generic.ScriptError("Real sprite parameters should be compile-time constants.")

    return RealSpriteAction(new_sprite)

sprite_template_map = {}

def parse_sprite_list(sprite_list, default_file, parameters = {}, mark_last = True):
    real_sprite_list = []
    for sprite in sprite_list:
        if isinstance(sprite, RealSprite):
            real_sprite_list.append(parse_real_sprite(sprite, default_file, parameters))
        else:
            real_sprite_list.extend(sprite.expand(default_file, parameters))
    if mark_last: real_sprite_list[-1].last = True
    return real_sprite_list
