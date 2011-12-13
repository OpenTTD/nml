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
from nml.ast import base_statement

class BaseSprite(base_statement.BaseStatement):
    """
    AST node for a 'base_sprite' block.
    NML syntax: base_sprite [block_name]([default_file]) { ..real sprites.. }

    @ivar param_list: List of parameters passed to the replace-block
    @type param_list: C{list} of L{Expression}

    @ivar sprite_list: List of real sprites to use
    @type sprite_list: Heterogeneous C{list} of L{RealSprite}, L{TemplateUsage}

    @ivar pcx: Default image file to use for sprites. Extracted from C{param_list} during pre-processing.
    @type pcx: C{None} if not specified, else L{StringLiteral}

    @ivar name: Name of this block.
    @type name: C{None] if not given, else C{str}
    """
    def __init__(self, param_list, sprite_list, name, pos):
        base_statement.BaseStatement.__init__(self, "base_sprites-block", pos)
        self.param_list = param_list
        self.sprite_list = sprite_list
        self.sprite_num = None
        self.name = name

    def pre_process(self):
        num_params = len(self.param_list)
        if not (0 <= num_params <= 2):
            raise generic.ScriptError("base_sprites-block requires 0 to 2 parameters, encountered %d" % num_params, self.pos)
        if num_params >= 2:
            self.sprite_num = self.param_list[0].reduce_constant()
        if num_params >= 1:
            self.pcx = self.param_list[-1].reduce()
            if not isinstance(self.pcx, expression.StringLiteral):
                raise generic.ScriptError("The last base_sprites-block parameter 'file' must be a string literal", self.pcx.pos)
        else:
            self.pcx = None

    def debug_print(self, indentation):
        print indentation*' ' + 'Base_sprite-block'
        print (indentation+2)*' ' + 'Source:', self.pcx.value if self.pcx is not None else 'None'
        if self.name: print (indentation+2)*' ' + 'Name:', self.name
        print (indentation+2)*' ' + 'Sprites:'
        for sprite in self.sprite_list:
            sprite.debug_print(indentation + 4)

    def get_action_list(self):
        actions = real_sprite.parse_sprite_list(self.sprite_list, self.pcx, block_name = self.name)
        actions[0].sprite_num = self.sprite_num
        return actions

    def __str__(self):
        name = str(self.name) if self.name is not None else ""
        ret = "base_sprites %s(%s) {\n" % (name, ", ".join([str(param) for param in self.param_list]))
        for sprite in self.sprite_list:
            ret += "\t%s\n" % str(sprite)
        ret += "}\n"
        return ret
