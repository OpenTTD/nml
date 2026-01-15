# SPDX-License-Identifier: GPL-2.0-or-later

from nml import expression, generic
from nml.actions import action12
from nml.ast import base_statement, sprite_container


class FontGlyphBlock(base_statement.BaseStatement, sprite_container.SpriteContainer):
    """
    AST class for a font_glyph block
    Syntax: font_glyph(

    @ivar font_size: Size of the font to provide characters for (NORMAL/SMALL/LARGE/MONO)
    @type font_size: L{Expression}

    @ivar base_char: First character to replace
    @type base_char: L{Expression}

    @ivar image_file: Default file to use for the contained real sprites (none if N/A)
    @type image_file: L{StringLiteral} or C{None}

    @ivar sprite_list: List of real sprites
    @type sprite_list: C{list} of L{RealSprite}
    """

    def __init__(self, param_list, sprite_list, name, pos):
        base_statement.BaseStatement.__init__(self, "font_glyph-block", pos)
        sprite_container.SpriteContainer.__init__(self, "font_glyph-block", name)
        if not (2 <= len(param_list) <= 3):
            raise generic.ScriptError(
                "font_glyph-block requires 2 or 3 parameters, encountered " + str(len(param_list)), pos
            )
        self.font_size = param_list[0]
        self.base_char = param_list[1]
        self.image_file = param_list[2].reduce() if len(param_list) >= 3 else None
        if self.image_file is not None and not isinstance(self.image_file, expression.StringLiteral):
            raise generic.ScriptError(
                "font_glyph-block parameter 3 'file' must be a string literal", self.image_file.pos
            )
        self.sprite_list = sprite_list
        self.add_sprite_data(self.sprite_list, self.image_file, pos)

    def debug_print(self, indentation):
        generic.print_dbg(indentation, "Load font glyphs, starting at", self.base_char)
        generic.print_dbg(indentation + 2, "Font size:  ", self.font_size)
        generic.print_dbg(
            indentation + 2, "Source:  ", self.image_file.value if self.image_file is not None else "None"
        )

        generic.print_dbg(indentation + 2, "Sprites:")
        for sprite in self.sprite_list:
            sprite.debug_print(indentation + 4)

    def get_action_list(self):
        return action12.parse_action12(self)

    def __str__(self):
        name = str(self.block_name) if self.block_name is not None else ""
        params = [self.font_size, self.base_char]
        if self.image_file is not None:
            params.append(self.image_file)
        ret = "font_glyph {}({}) {{\n".format(name, ", ".join(str(param) for param in params))
        for sprite in self.sprite_list:
            ret += "\t{}\n".format(sprite)
        ret += "}\n"
        return ret
