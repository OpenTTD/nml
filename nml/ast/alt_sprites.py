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

from nml import expression, generic, global_constants
from nml.actions import real_sprite
from nml.ast import base_statement
import os, Image

"""
Store if there are any 32bpp sprites,
if so ask to enable the 32bpp blitter via action14
"""
any_32bpp_sprites = False

class AltSpritesBlock(base_statement.BaseStatement):
    """
    AST Node for alternative graphics. These are normally 32bpp graphics, possible
    for a higher zoom-level than the default sprites.

    @ivar name: The name of the replace/font_glyph/replace_new/spriteblock-block this
                block contains alternative graphics for.
    @type name: L{expression.Identifier}

    @ivar zoom_level: The zoomlevel these graphics are for.
    @type zoom_level: L{expression.Expression}

    @ivar pcx: Default graphics file for the sprites in this block.
    @type pcx: L{expression.StringLiteral} or C{None}

    @ivar sprite_list: List of real sprites or templates expanding to real sprites.
    @type sprite_list: Heterogeneous C{list} of L{RealSprite}, L{TemplateUsage}
    """
    def __init__(self, param_list, sprite_list, pos):
        base_statement.BaseStatement.__init__(self, "alt_sprites-block", pos)
        if not (2 <= len(param_list) <= 3):
            raise generic.ScriptError("alternative_sprites-block requires 2 or 3 parameters, encountered " + str(len(param_list)), pos)
        self.name = param_list[0]
        self.zoom_level = param_list[1]
        self.pcx = param_list[2] if len(param_list) >= 3 else None
        self.sprite_list = sprite_list
        any_32bpp_sprites = True


    def pre_process(self):
        if self.pcx:
            self.pcx.reduce()
            if not isinstance(self.pcx, expression.StringLiteral):
                raise generic.ScriptError("alternative_sprites-block parameter 3 'file' must be a string literal", self.pcx.pos)

    def debug_print(self, indentation):
        print indentation*' ' + 'Alternative sprites'
        print (indentation+2)*' ' + 'Replacement for sprite:', str(self.name)
        print (indentation+2)*' ' + 'Zoom level:', str(self.zoom_level)
        print (indentation+2)*' ' + 'Source:', self.pcx.value if self.pcx is not None else 'None'
        print (indentation+2)*' ' + 'Sprites:'
        for sprite in self.sprite_list:
            sprite.debug_print(indentation + 4)

    def get_action_list(self):
        return []

