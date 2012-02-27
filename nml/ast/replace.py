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
from nml.ast import base_statement, sprite_container

class ReplaceSprite(base_statement.BaseStatement, sprite_container.SpriteContainer):
    """
    AST node for a 'replace' block.
    NML syntax: replace [name] (start_id[, default_file]) { ..real sprites.. }

    @ivar start_id: First sprite to replace. Extracted from C{param_list} during pre-processing.
    @type start_id: C{Expression}

    @ivar image_file: Default image file to use for sprites.
    @type image_file: C{None} if not specified, else L{StringLiteral}

    @ivar sprite_list: List of real sprites to use
    @type sprite_list: Heterogeneous C{list} of L{RealSprite}, L{TemplateUsage}
    """
    def __init__(self, param_list, sprite_list, name, pos):
        base_statement.BaseStatement.__init__(self, "replace-block", pos)
        sprite_container.SpriteContainer.__init__(self, "replace-block", name)

        num_params = len(param_list)
        if not (1 <= num_params <= 2):
            raise generic.ScriptError("replace-block requires 1 or 2 parameters, encountered " + str(num_params), pos)
        self.start_id = param_list[0]
        if num_params >= 2:
            self.image_file = param_list[1].reduce()
            if not isinstance(self.image_file, expression.StringLiteral):
                raise generic.ScriptError("replace-block parameter 2 'file' must be a string literal", self.image_file.pos)
        else:
            self.image_file = None
        self.sprite_list = sprite_list
        self.add_sprite_data(self.sprite_list, self.image_file, pos)

    def pre_process(self):
        self.start_id = self.start_id.reduce(global_constants.const_list)

    def debug_print(self, indentation):
        print indentation*' ' + 'Replace sprites starting at'
        self.start_id.debug_print(indentation+2)
        print (indentation+2)*' ' + 'Source:', self.image_file.value if self.image_file is not None else 'None'
        if self.block_name is not None:
            print (indentation+2)*' ' + 'Name:', self.block_name.value
        print (indentation+2)*' ' + 'Sprites:'
        for sprite in self.sprite_list:
            sprite.debug_print(indentation + 4)

    def get_action_list(self):
        return actionA.parse_actionA(self)

    def __str__(self):
        name = str(self.block_name) if self.block_name is not None else ""
        def_file = "" if self.image_file is None else ", " + str(self.image_file)
        ret = "replace %s(%s%s) {\n" % (name, str(self.start_id), def_file)
        for sprite in self.sprite_list:
            ret += "\t%s\n" % str(sprite)
        ret += "}\n"
        return ret

class ReplaceNewSprite(base_statement.BaseStatement, sprite_container.SpriteContainer):
    """
    AST node for a 'replacenew' block.
    NML syntax: replacenew [name](type[, default_file[, offset]]) { ..real sprites.. }

    @ivar type: Type of sprites to replace.
    @type type: L{Identifier}

    @ivar image_file: Default image file to use for sprites.
    @type image_file: C{None} if not specified, else L{StringLiteral}

    @ivar offset: Offset into the block of sprites.
    @type offset: C{int}

    @ivar sprite_list: List of real sprites to use
    @type sprite_list: Heterogeneous C{list} of L{RealSprite}, L{TemplateUsage}
    """
    def __init__(self, param_list, sprite_list, name, pos):
        base_statement.BaseStatement.__init__(self, "replacenew-block", pos)
        sprite_container.SpriteContainer.__init__(self, "replacenew-block", name)
        num_params = len(param_list)
        if not (1 <= num_params <= 3):
            raise generic.ScriptError("replacenew-block requires 1 to 3 parameters, encountered " + str(num_params), pos)

        self.type = param_list[0]
        if not isinstance(self.type, expression.Identifier):
            raise generic.ScriptError("replacenew parameter 'type' must be an identifier of a sprite replacement type", self.type.pos)

        if num_params >= 2:
            self.image_file = param_list[1].reduce()
            if not isinstance(self.image_file, expression.StringLiteral):
                raise generic.ScriptError("replacenew-block parameter 2 'file' must be a string literal", self.image_file.pos)
        else:
            self.image_file = None

        if num_params >= 3:
            self.offset = param_list[2].reduce_constant().value
            generic.check_range(self.offset, 0, 0xFFFF, "replacenew-block parameter 3 'offset'", param_list[2].pos)
        else:
            self.offset = 0

        self.sprite_list = sprite_list
        self.add_sprite_data(self.sprite_list, self.image_file, pos)

    def debug_print(self, indentation):
        print indentation*' ' + 'Replace sprites for new features of type', self.type
        print (indentation+2)*' ' + 'Offset:  ', self.offset
        print (indentation+2)*' ' + 'Source:  ', self.image_file.value if self.image_file is not None else 'None'
        if self.block_name is not None:
            print (indentation+2)*' ' + 'Name:', self.block_name.value
        print (indentation+2)*' ' + 'Sprites:'
        for sprite in self.sprite_list:
            sprite.debug_print(indentation + 4)

    def get_action_list(self):
        return action5.parse_action5(self)

    def __str__(self):
        name = str(self.block_name) if self.block_name is not None else ""
        params = [self.type]
        if self.image_file is not None:
            params.append(self.image_file)
            if self.offset != 0:
                params.append(self.offset)
        ret = "replacenew %s(%s) {\n" % (name, ", ".join([str(param) for param in params]))
        for sprite in self.sprite_list:
            ret += "\t%s\n" % str(sprite)
        ret += "}\n"
        return ret

