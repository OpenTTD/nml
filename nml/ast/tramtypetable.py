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

class TramtypeTable(base_statement.BaseStatement):
    def __init__(self, tramtype_list, pos):
        base_statement.BaseStatement.__init__(self, "tram type table", pos, False, False)
        self.tramtype_list = tramtype_list
        generic.OnlyOnce.enforce(self, "tram type table")
        global_constants.is_default_tramtype_table = False
        global_constants.tramtype_table.clear()

    def register_names(self):
        for i, tramtype in enumerate(self.tramtype_list):
            if isinstance(tramtype, assignment.Assignment):
                name = tramtype.name
                val_list = []
                for rt in tramtype.value:
                    if isinstance(rt, expression.Identifier):
                        val_list.append(expression.StringLiteral(rt.value, rt.pos))
                    else:
                        val_list.append(rt)
                    expression.parse_string_to_dword(val_list[-1]) # we don't care about the result, only validate the input
                self.tramtype_list[i] = val_list if len(val_list) > 1 else val_list[0]
            else:
                name = tramtype
                if isinstance(tramtype, expression.Identifier):
                    self.tramtype_list[i] = expression.StringLiteral(tramtype.value, tramtype.pos)
                expression.parse_string_to_dword(self.tramtype_list[i]) # we don't care about the result, only validate the input
            global_constants.tramtype_table[name.value] = i

    def pre_process(self):
        pass

    def debug_print(self, indentation):
        generic.print_dbg(indentation, 'Tramtype table')
        for tramtype in self.tramtype_list:
            generic.print_dbg(indentation + 2, 'Tramtype: ', tramtype.value)

    def get_action_list(self):
        return action0.get_tramtypelist_action(self.tramtype_list)

    def __str__(self):
        ret = 'tramtypetable {\n'
        ret += ', '.join([expression.identifier_to_print(tramtype.value) for tramtype in self.tramtype_list])
        ret += '\n}\n'
        return ret
