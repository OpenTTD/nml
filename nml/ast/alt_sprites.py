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
from nml.ast import base_statement, sprite_container

"""
Store if there are any 32bpp sprites,
if so ask to enable the 32bpp blitter via action14
"""
any_32bpp_sprites = False

zoom_levels = {
    "ZOOM_LEVEL_NORMAL": 0,
    "ZOOM_LEVEL_IN_4X": 1,
    "ZOOM_LEVEL_IN_2X": 2,
    "ZOOM_LEVEL_OUT_2X": 3,
    "ZOOM_LEVEL_OUT_4X": 4,
    "ZOOM_LEVEL_OUT_8X": 5,
}
allow_extra_zoom = True

bit_depths = {"BIT_DEPTH_8BPP": 8, "BIT_DEPTH_32BPP": 32.0}
allow_32bpp = True


class AltSpritesBlock(base_statement.BaseStatement):
    """
    AST Node for alternative graphics. These are normally 32bpp graphics, possible
    for a higher zoom-level than the default sprites.
    Syntax: alternative_sprites(name, zoom_level, bit_depth[, image_file])

    @ivar name: The name of the replace/font_glyph/replace_new/spriteset/base_graphics-block this
                block contains alternative graphics for.
    @type name: L{expression.Identifier}

    @ivar zoom_level: The zoomlevel these graphics are for.
    @type zoom_level: C{int}

    @ivar bit_depth: Bit depth these graphics are for
    @type bit_depth: C{int}

    @ivar image_file: Default graphics file for the sprites in this block.
    @type image_file: L{expression.StringLiteral} or C{None}

    @ivar mask_file: Default graphics file for the mask sprites in this block.
    @type mask_file: L{expression.StringLiteral} or C{None}

    @ivar sprite_list: List of real sprites or templates expanding to real sprites.
    @type sprite_list: Heterogeneous C{list} of L{RealSprite}, L{TemplateUsage}
    """

    def __init__(self, param_list, sprite_list, pos):
        base_statement.BaseStatement.__init__(self, "alt_sprites-block", pos)
        if not (3 <= len(param_list) <= 5):
            raise generic.ScriptError(
                "alternative_sprites-block requires 3 or 4 parameters, encountered " + str(len(param_list)), pos
            )

        self.name = param_list[0]
        if not isinstance(self.name, expression.Identifier):
            raise generic.ScriptError("alternative_sprites parameter 1 'name' must be an identifier", self.name.pos)

        if isinstance(param_list[1], expression.Identifier) and param_list[1].value in zoom_levels:
            self.zoom_level = zoom_levels[param_list[1].value]
        else:
            raise generic.ScriptError(
                "value for alternative_sprites parameter 2 'zoom level' is not a valid zoom level", param_list[1].pos
            )

        if isinstance(param_list[2], expression.Identifier) and param_list[2].value in bit_depths:
            self.bit_depth = bit_depths[param_list[2].value]
        else:
            raise generic.ScriptError(
                "value for alternative_sprites parameter 3 'bit depth' is not a valid bit depthl", param_list[2].pos
            )
        global any_32bpp_sprites
        if self.bit_depth == 32:
            any_32bpp_sprites = allow_32bpp

        if len(param_list) >= 4:
            self.image_file = param_list[3].reduce()
            if not isinstance(self.image_file, expression.StringLiteral):
                raise generic.ScriptError(
                    "alternative_sprites-block parameter 4 'file' must be a string literal", self.image_file.pos
                )
        else:
            self.image_file = None

        if len(param_list) >= 5:
            self.mask_file = param_list[4].reduce()
            if not isinstance(self.mask_file, expression.StringLiteral):
                raise generic.ScriptError(
                    "alternative_sprites-block parameter 5 'mask_file' must be a string literal", self.mask_file.pos
                )
            if not self.bit_depth == 32:
                raise generic.ScriptError("A mask file may only be specified for 32 bpp sprites.", self.mask_file.pos)
        else:
            self.mask_file = None

        self.sprite_list = sprite_list

    def pre_process(self):
        if (self.bit_depth == 32 and not allow_32bpp) or (self.zoom_level != 0 and not allow_extra_zoom):
            return
        block = sprite_container.SpriteContainer.resolve_sprite_block(self.name)
        block.add_sprite_data(
            self.sprite_list, self.image_file, self.pos, self.zoom_level, self.bit_depth, self.mask_file
        )

    def debug_print(self, indentation):
        generic.print_dbg(indentation, "Alternative sprites")
        generic.print_dbg(indentation + 2, "Replacement for sprite:", self.name)
        generic.print_dbg(indentation + 2, "Zoom level:", self.zoom_level)
        generic.print_dbg(indentation + 2, "Bit depth:", self.bit_depth)
        generic.print_dbg(indentation + 2, "Source:", self.image_file.value if self.image_file is not None else "None")
        generic.print_dbg(
            indentation + 2, "Mask source:", self.mask_file.value if self.mask_file is not None else "None"
        )

        generic.print_dbg(indentation + 2, "Sprites:")
        for sprite in self.sprite_list:
            sprite.debug_print(indentation + 4)

    def get_action_list(self):
        return []

    def __str__(self):
        params = [
            self.name,
            generic.reverse_lookup(zoom_levels, self.zoom_level),
            generic.reverse_lookup(bit_depths, self.bit_depth),
        ]
        if self.image_file is not None:
            params.append(self.image_file)
        if self.mask_file is not None:
            params.append(self.mask_file)
        ret = "alternative_sprites({}) {{\n".format(", ".join(str(p) for p in params))
        for sprite in self.sprite_list:
            ret += "\t{}\n".format(sprite)
        ret += "}\n"
        return ret
