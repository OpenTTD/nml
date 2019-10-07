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

from nml import generic, global_constants, expression
from nml.ast import assignment
from nml.actions import action0
from nml.ast import base_statement

class RoadtypeTable(base_statement.BaseStatement):
    def __init__(self, roadtype_list, pos):
        base_statement.BaseStatement.__init__(self, "road type table", pos, False, False)
        self.roadtype_list = roadtype_list
        generic.OnlyOnce.enforce(self, "road type table")
        global_constants.is_default_roadtype_table = False
        global_constants.roadtype_table.clear()

    def register_names(self):
        for i, roadtype in enumerate(self.roadtype_list):
            if isinstance(roadtype, assignment.Assignment):
                name = roadtype.name
                val_list = []
                for rt in roadtype.value:
                    if isinstance(rt, expression.Identifier):
                        val_list.append(expression.StringLiteral(rt.value, rt.pos))
                    else:
                        val_list.append(rt)
                    expression.parse_string_to_dword(val_list[-1]) # we don't care about the result, only validate the input
                self.roadtype_list[i] = val_list if len(val_list) > 1 else val_list[0]
            else:
                name = roadtype
                if isinstance(roadtype, expression.Identifier):
                    self.roadtype_list[i] = expression.StringLiteral(roadtype.value, roadtype.pos)
                expression.parse_string_to_dword(self.roadtype_list[i]) # we don't care about the result, only validate the input
            global_constants.roadtype_table[name.value] = i

    def pre_process(self):
        pass

    def debug_print(self, indentation):
        generic.print_dbg(indentation, 'Roadtype table')
        for roadtype in self.roadtype_list:
            generic.print_dbg(indentation + 2, 'Roadtype: ', roadtype.value)

    def get_action_list(self):
        return action0.get_roadtypelist_action(self.roadtype_list)

    def __str__(self):
        ret = 'roadtypetable {\n'
        ret += ', '.join([expression.identifier_to_print(roadtype.value) for roadtype in self.roadtype_list])
        ret += '\n}\n'
        return ret
