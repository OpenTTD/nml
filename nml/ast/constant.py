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
from nml.ast import base_statement


class Constant(base_statement.BaseStatement):
    def __init__(self, name, value):
        base_statement.BaseStatement.__init__(self, "constant", name.pos, False, False)
        self.name = name
        self.value = value

    def register_names(self):
        if not isinstance(self.name, expression.Identifier):
            raise generic.ScriptError("Constant name should be an identifier", self.name.pos)
        if self.name.value in global_constants.constant_numbers:
            raise generic.ScriptError("Redefinition of constant '{}'.".format(self.name.value), self.name.pos)
        global_constants.constant_numbers[self.name.value] = self.value.reduce_constant(
            global_constants.const_list
        ).value

    def debug_print(self, indentation):
        generic.print_dbg(indentation, "Constant")
        generic.print_dbg(indentation + 2, "Name:")
        self.name.debug_print(indentation + 4)

        generic.print_dbg(indentation + 2, "Value:")
        self.value.debug_print(indentation + 4)

    def get_action_list(self):
        return []

    def __str__(self):
        return "const {} = {};".format(self.name, self.value)
