from nml import generic
from real_sprite import *

class Action12(object):

    #sets: list of (font_size, num_char, base_char) tuples
    def __init__(self, sets):
        self.sets = sets

    def prepare_output(self):
        pass

    def write(self, file):
        #<sprite-number> * <length> 12 <num-def> (<font> <num-char> <base-char>){n}
        size = 2 + 4 * len(self.sets)
        file.print_sprite_size(size)
        file.print_bytex(0x12)
        file.print_byte(len(self.sets))
        file.newline()
        for font_size, num_char, base_char in self.sets:
            font_size.write(file, 1)
            file.print_byte(num_char)
            file.print_word(base_char)
            file.newline()
        file.newline()

    def skip_action7(self):
        return True

    def skip_action9(self):
        return True

    def skip_needed(self):
        return True

font_sizes = {
    'NORMAL' : 0,
    'SMALL'  : 1,
    'LARGE'  : 2,
}

def parse_action12(font_glpyhs):
    action_list = []

    try:
        font_size = reduce_constant(font_glpyhs.font_size, [font_sizes])
        base_char = reduce_constant(font_glpyhs.base_char)
    except generic.ConstError:
        raise generic.ScriptError("Parameters of font_glpyh have to be compile-time constants")
    if font_size.value not in font_sizes.values():
        raise generic.ScriptError("Invalid value for parameter 'font_size' in font_glpyh, valid values are 0, 1, 2")
    if not (0 <= base_char.value <= 0xFFFF):
        raise generic.ScriptError("Invalid value for parameter 'base_char' in font_glyph, valid values are 0-0xFFFF")

    real_sprite_list = parse_sprite_list(font_glpyhs.sprite_list)
    num_sprites = len(real_sprite_list);
    char = base_char.value
    last_char = char + num_sprites
    if last_char > 0xFFFF:
        raise generic.ScriptError("Character numbers in font_glyph block exceed the allowed range (0-0xFFFF)");

    sets = []
    while char < last_char:
        #each set of characters must fit in a single 128-char block, according to specs / TTDP
        if (char // 128) * 128 != (last_char // 128)  * 128:
            num_in_set = (char // 128 + 1) * 128 - char
        else:
            num_in_set = last_char - char
        sets.append((font_size, num_in_set, char))
        char += num_in_set

    action_list.append(Action12(sets))

    last_sprite = real_sprite_list[num_sprites - 1][0]
    for sprite, id_dict in real_sprite_list:
        action_list.append(parse_real_sprite(sprite, font_glpyhs.pcx, sprite == last_sprite, id_dict))

    return action_list
