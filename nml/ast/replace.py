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
from nml.actions import actionA, action5
from nml.ast import base_statement

class ReplaceSprite(base_statement.BaseStatement):
    """
    AST node for a 'replace' block.
    NML syntax: replace(start_id[, default_file]) { ..real sprites.. }

    @ivar param_list: List of parameters passed to the replace-block
    @type param_list: C{list} of L{Expression}

    @ivar sprite_list: List of real sprites to use
    @type sprite_list: Heterogeneous C{list} of L{RealSprite}, L{TemplateUsage}

    @ivar start_id: First sprite to replace. Extracted from C{param_list} during pre-processing.
    @type start_id: C{Expression}

    @ivar pcx: Default image file to use for sprites. Extracted from C{param_list} during pre-processing.
    @type pcx: C{None} if not specified, else L{StringLiteral}

    @ivar name: Name of this block.
    @type name: C{None] if not given, else C{str}
    """
    def __init__(self, param_list, sprite_list, name, pos):
        base_statement.BaseStatement.__init__(self, "replace-block", pos)
        self.param_list = param_list
        self.sprite_list = sprite_list
        self.name = name

    def pre_process(self):
        num_params = len(self.param_list)
        if not (1 <= num_params <= 2):
            raise generic.ScriptError("replace-block requires 1 or 2 parameters, encountered " + str(num_params), self.pos)
        self.start_id = self.param_list[0].reduce(global_constants.const_list)
        if num_params >= 2:
            self.pcx = self.param_list[1].reduce()
            if not isinstance(self.pcx, expression.StringLiteral):
                raise generic.ScriptError("replace-block parameter 2 'file' must be a string literal", self.pcx.pos)
        else:
            self.pcx = None

    def debug_print(self, indentation):
        print indentation*' ' + 'Replace sprites starting at'
        self.start_id.debug_print(indentation+2)
        print (indentation+2)*' ' + 'Source:', self.pcx.value if self.pcx is not None else 'None'
        if self.name: print (indentation+2)*' ' + 'Name:', self.name
        print (indentation+2)*' ' + 'Sprites:'
        for sprite in self.sprite_list:
            sprite.debug_print(indentation + 4)

    def get_action_list(self):
        return actionA.parse_actionA(self)

    def __str__(self):
        name = str(self.name) if self.name is not None else ""
        ret = "replace %s(%s) {\n" % (name, ", ".join([str(param) for param in self.param_list]))
        for sprite in self.sprite_list:
            ret += "\t%s\n" % str(sprite)
        ret += "}\n"
        return ret

class ReplaceNewSprite(base_statement.BaseStatement):
    """
    AST node for a 'replacenew' block.
    NML syntax: replacenew(type[, default_file[, offset]]) { ..real sprites.. }

    @ivar param_list: List of parameters passed to the replacenew-block
    @type param_list: C{list} of L{Expression}

    @ivar sprite_list: List of real sprites to use
    @type sprite_list: Heterogeneous C{list} of L{RealSprite}, L{TemplateUsage}

    @ivar type: Type of sprites to replace. Extracted from C{param_list} during pre-processing.
    @type type: L{Identifier}

    @ivar pcx: Default image file to use for sprites. Extracted from C{param_list} during pre-processing.
    @type pcx: C{None} if not specified, else L{StringLiteral}

    @ivar offset: Offset into the block of sprites. Extracted from C{param_list} during pre-processing.
    @type offset: C{int}

    @ivar name: Name of this block.
    @type name: C{None] if not given, else C{str}
    """
    def __init__(self, param_list, sprite_list, name, pos):
        base_statement.BaseStatement.__init__(self, "replacenew-block", pos)
        self.param_list = param_list
        self.sprite_list = sprite_list
        self.name = name

    def pre_process(self):
        num_params = len(self.param_list)
        if not (1 <= num_params <= 3):
            raise generic.ScriptError("replacenew-block requires 1 to 3 parameters, encountered " + str(num_params), self.pos)

        self.type = self.param_list[0]
        if not isinstance(self.type, expression.Identifier):
            raise generic.ScriptError("replacenew parameter 'type' must be an identifier of a sprite replacement type", self.type.pos)
            

        if num_params >= 2:
            self.pcx = self.param_list[1].reduce()
            if not isinstance(self.pcx, expression.StringLiteral):
                raise generic.ScriptError("replacenew-block parameter 2 'file' must be a string literal", self.pcx.pos)
        else:
            self.pcx = None

        if num_params >= 3:
            self.offset = self.param_list[2].reduce_constant().value
            generic.check_range(self.offset, 0, 0xFFFF, "replacenew-block parameter 3 'offset'", self.param_list[2].pos)
        else:
            self.offset = 0

    def debug_print(self, indentation):
        print indentation*' ' + 'Replace sprites for new features of type', self.type
        print (indentation+2)*' ' + 'Offset:  ', self.offset
        print (indentation+2)*' ' + 'Source:  ', self.pcx.value if self.pcx is not None else 'None'
        print (indentation+2)*' ' + 'Sprites:'
        for sprite in self.sprite_list:
            sprite.debug_print(indentation + 4)

    def get_action_list(self):
        return action5.parse_action5(self)

    def __str__(self):
        name = str(self.name) if self.name is not None else ""
        ret = "replacenew %s(%s) {\n" % (name, ", ".join([str(param) for param in self.param_list]))
        for sprite in self.sprite_list:
            ret += "\t%s\n" % str(sprite)
        ret += "}\n"
        return ret

