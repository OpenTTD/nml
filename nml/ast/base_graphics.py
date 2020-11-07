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
from nml.actions import real_sprite
from nml.ast import base_statement, sprite_container


class BaseGraphics(base_statement.BaseStatement, sprite_container.SpriteContainer):
    """
    AST node for a 'base_graphics' block.
    NML syntax: base_graphics [block_name]([[sprite_num ,]default_file]) { ..real sprites.. }

    @ivar image_file: Default image file to use for sprites.
    @type image_file: C{None} if not specified, else L{StringLiteral}

    @ivar sprite_num: Sprite number of the first sprite (if provided explicitly)
    @type sprite_num: L{Expression} or C{None}

    @ivar sprite_list: List of real sprites to use
    @type sprite_list: Heterogeneous C{list} of L{RealSprite}, L{TemplateUsage}
    """

    def __init__(self, param_list, sprite_list, name, pos):
        base_statement.BaseStatement.__init__(self, "base_graphics-block", pos)
        sprite_container.SpriteContainer.__init__(self, "base_graphics-block", name)

        num_params = len(param_list)
        if not (0 <= num_params <= 2):
            raise generic.ScriptError(
                "base_graphics-block requires 0 to 2 parameters, encountered {:d}".format(num_params), pos
            )
        if num_params >= 2:
            self.sprite_num = param_list[0].reduce_constant()
        else:
            self.sprite_num = None

        if num_params >= 1:
            self.image_file = param_list[-1].reduce()
            if not isinstance(self.image_file, expression.StringLiteral):
                raise generic.ScriptError(
                    "The last base_graphics-block parameter 'file' must be a string literal", self.image_file.pos
                )
        else:
            self.image_file = None
        self.sprite_list = sprite_list
        self.add_sprite_data(self.sprite_list, self.image_file, pos)

    def debug_print(self, indentation):
        generic.print_dbg(indentation, "base_graphics-block")
        generic.print_dbg(indentation + 2, "Source:", self.image_file.value if self.image_file is not None else "None")
        if self.block_name:
            generic.print_dbg(indentation + 2, "Name:", self.block_name)
        if self.sprite_num is not None:
            generic.print_dbg(indentation + 2, "Sprite number:", self.sprite_num)

        generic.print_dbg(indentation + 2, "Sprites:")
        for sprite in self.sprite_list:
            sprite.debug_print(indentation + 4)

    def get_action_list(self):
        actions = real_sprite.parse_sprite_data(self)
        actions[0].sprite_num = self.sprite_num
        return actions

    def __str__(self):
        name = str(self.block_name) if self.block_name is not None else ""
        params = [] if self.sprite_num is None else [self.sprite_num]
        if self.image_file is not None:
            params.append(self.image_file)
        ret = "base_graphics {}({}) {{\n".format(name, ", ".join(str(param) for param in params))
        for sprite in self.sprite_list:
            ret += "\t{}\n".format(sprite)
        ret += "}\n"
        return ret
