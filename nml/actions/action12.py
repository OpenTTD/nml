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

from nml import expression, generic
from nml.actions import base_action, real_sprite


class Action12(base_action.BaseAction):

    # sets: list of (font_size, num_char, base_char) tuples
    def __init__(self, sets):
        self.sets = sets

    def write(self, file):
        # <sprite-number> * <length> 12 <num-def> (<font> <num-char> <base-char>){n}
        size = 2 + 4 * len(self.sets)
        file.start_sprite(size)
        file.print_bytex(0x12)
        file.print_byte(len(self.sets))
        file.newline()
        for font_size, num_char, base_char in self.sets:
            font_size.write(file, 1)
            file.print_byte(num_char)
            file.print_word(base_char)
            file.newline()
        file.end_sprite()


font_sizes = {
    "NORMAL": 0,
    "SMALL": 1,
    "LARGE": 2,
    "MONO": 3,
}


def parse_action12(font_glyphs):
    try:
        font_size = font_glyphs.font_size.reduce_constant([font_sizes])
        if isinstance(font_glyphs.base_char, expression.StringLiteral) and len(font_glyphs.base_char.value) == 1:
            base_char = ord(font_glyphs.base_char.value)
        else:
            base_char = font_glyphs.base_char.reduce_constant()
    except generic.ConstError:
        raise generic.ScriptError("Parameters of font_glyph have to be compile-time constants", font_glyphs.pos)
    if font_size.value not in font_sizes.values():
        raise generic.ScriptError(
            "Invalid value for parameter 'font_size' in font_glyph, valid values are 0, 1, 2", font_size.pos
        )
    if not (0 <= base_char.value <= 0xFFFF):
        raise generic.ScriptError(
            "Invalid value for parameter 'base_char' in font_glyph, valid values are 0-0xFFFF", base_char.pos
        )

    real_sprite_list = real_sprite.parse_sprite_data(font_glyphs)
    char = base_char.value
    last_char = char + len(real_sprite_list)
    if last_char > 0xFFFF:
        raise generic.ScriptError(
            "Character numbers in font_glyph block exceed the allowed range (0-0xFFFF)", font_glyphs.pos
        )

    sets = []
    while char < last_char:
        # each set of characters must fit in a single 128-char block, according to specs / TTDP
        if (char // 128) * 128 != (last_char // 128) * 128:
            num_in_set = (char // 128 + 1) * 128 - char
        else:
            num_in_set = last_char - char
        sets.append((font_size, num_in_set, char))
        char += num_in_set

    return [Action12(sets)] + real_sprite_list
