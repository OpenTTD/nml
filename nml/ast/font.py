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

from nml import expression, generic, expression
from nml.actions import action12
from nml.ast import base_statement

class FontGlyphBlock(base_statement.BaseStatement):
    def __init__(self, param_list, sprite_list, name, pos):
        base_statement.BaseStatement.__init__(self, "font_glpyh-block", pos)
        if not (2 <= len(param_list) <= 3):
            raise generic.ScriptError("font_glpyh-block requires 2 or 3 parameters, encountered " + str(len(param_list)), pos)
        self.font_size = param_list[0]
        self.base_char = param_list[1]
        self.pcx = param_list[2] if len(param_list) >= 3 else None
        self.sprite_list = sprite_list
        self.name = name

    def pre_process(self):
        if self.pcx:
            self.pcx.reduce()
            if not isinstance(self.pcx, expression.StringLiteral):
                raise generic.ScriptError("font_glpyh-block parameter 3 'file' must be a string literal", self.pcx.pos)

    def debug_print(self, indentation):
        print indentation*' ' + 'Load font glyphs, starting at', self.base_char
        print (indentation+2)*' ' + 'Font size:  ', self.font_size
        print (indentation+2)*' ' + 'Source:  ', self.pcx.value if self.pcx is not None else 'None'
        print (indentation+2)*' ' + 'Sprites:'
        for sprite in self.sprite_list:
            sprite.debug_print(indentation + 4)

    def get_action_list(self):
        return action12.parse_action12(self)
