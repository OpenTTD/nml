import nml.ast
from nml import generic
from nml.expression import *

class RealSpriteAction(object):
    def __init__(self, sprite, pcx, last = False):
        self.sprite = sprite
        self.pcx = pcx
        self.last = last

    def prepare_output(self):
        pass

    def write(self, file):
        if self.sprite.is_empty:
            file.print_empty_realsprite()
            file.newline()
            if self.last: file.newline()
            return
        file.print_sprite(self.pcx, self.sprite)
        file.newline()
        if self.last: file.newline()

    def skip_action7(self):
        return True

    def skip_action9(self):
        return True

    def skip_needed(self):
        return True

real_sprite_compression_flags = {
    'NORMAL'       : 0x00,
    'TILE'         : 0x08,
    'UNCOMPRESSED' : 0x00,
    'COMPRESSED'   : 0x02,
    'CROP'         : 0x00,
    'NOCROP'       : 0x40,
}


def parse_real_sprite(sprite, pcx, last, id_dict):
    if len(sprite.param_list) == 0:
        sprite.is_empty = True
        return RealSpriteAction(sprite, pcx, last)
    elif not 6 <= len(sprite.param_list) <= 7:
        raise generic.ScriptError("Invalid number of arguments for real sprite. Expected 6 or 7.")
    try:
        # create new sprite struct, needed for template expansion
        new_sprite = nml.ast.RealSprite()

        new_sprite.xpos  = reduce_constant(sprite.param_list[0], [id_dict])
        new_sprite.ypos  = reduce_constant(sprite.param_list[1], [id_dict])
        new_sprite.xsize = reduce_constant(sprite.param_list[2], [id_dict])
        new_sprite.ysize = reduce_constant(sprite.param_list[3], [id_dict])
        new_sprite.xrel  = reduce_constant(sprite.param_list[4], [id_dict])
        new_sprite.yrel  = reduce_constant(sprite.param_list[5], [id_dict])

        generic.check_range(new_sprite.xpos.value,  0, 0x7fffFFFF,   "Real sprite paramater 'xpos'")
        generic.check_range(new_sprite.ypos.value,  0, 0x7fffFFFF,   "Real sprite paramater 'ypos'")
        generic.check_range(new_sprite.xsize.value, 1, 0xFFFF,       "Real sprite paramater 'xsize'")
        generic.check_range(new_sprite.ysize.value, 1, 0xFF,         "Real sprite paramater 'ysize'")
        generic.check_range(new_sprite.xrel.value, -0x8000, 0x7fff,  "Real sprite paramater 'xrel'")
        generic.check_range(new_sprite.yrel.value, -0x8000, 0x7fff,  "Real sprite paramater 'yrel'")

        if len(sprite.param_list) == 7:
            new_sprite.compression = reduce_constant(sprite.param_list[6], [real_sprite_compression_flags, id_dict])
            new_sprite.compression.value |= 0x01
        else:
            new_sprite.compression = ConstantNumeric(0x01)
        # only bits 0, 1, 3, and 6 can be set
        if (new_sprite.compression.value & ~0x4B) != 0:
            raise generic.ScriptError("Real sprite compression is invalid; can only have bit 0, 1, 3 and/or 6 set, encountered " + str(new_sprite.compression.value))
    except generic.ConstError:
        raise generic.ScriptError("Real sprite parameters should be compile-time constants.")

    return RealSpriteAction(new_sprite, pcx, last)

sprite_template_map = {}

def parse_sprite_list(sprite_list):
    real_sprite_list = []
    for sprite in sprite_list:
        if isinstance(sprite, nml.ast.RealSprite):
            real_sprite_list.append((sprite, {}))
        else:
            #expand template
            assert isinstance(sprite, nml.ast.TemplateUsage)
            if sprite.name.value not in sprite_template_map:
                raise generic.ScriptError("Encountered unknown template identifier: " + sprite.name.value)
            template = sprite_template_map[sprite.name.value]
            if len(sprite.param_list) != len(template.param_list):
                raise generic.ScriptError("Incorrect number of template arguments. Expected " + str(len(template.param_list)) + ", got " + str(len(sprite.param_list)))
            param_dict = {}
            try:
                i = 0
                for param in sprite.param_list:
                    param = reduce_constant(param, [real_sprite_compression_flags])
                    param_dict[template.param_list[i].value] = param.value
                    i += 1
            except ConstError:
                raise generic.ScriptError("Template parameters should be compile-time constants")
            for sprite in template.sprite_list:
                real_sprite_list.append((sprite, param_dict))
    return real_sprite_list
