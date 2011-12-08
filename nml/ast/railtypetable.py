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

class RailtypeTable(base_statement.BaseStatement):
    def __init__(self, railtype_list, pos):
        base_statement.BaseStatement.__init__(self, "rail type table", pos, False, False)
        self.railtype_list = railtype_list
        generic.OnlyOnce.enforce(self, "rail type table")
        global_constants.railtype_table.clear()

    def register_names(self):
        for i, railtype in enumerate(self.railtype_list):
            if isinstance(railtype, assignment.Assignment):
                name = railtype.name
                val_list = []
                for rt in railtype.value:
                    if isinstance(rt, expression.Identifier):
                        val_list.append(expression.StringLiteral(rt.value, rt.pos))
                    else:
                        val_list.append(rt)
                    expression.parse_string_to_dword(val_list[-1])
                self.railtype_list[i] = val_list if len(val_list) > 1 else val_list[0]
            else:
                name = railtype
                if isinstance(railtype, expression.Identifier):
                    self.railtype_list[i] = expression.StringLiteral(railtype.value, railtype.pos)
                expression.parse_string_to_dword(self.railtype_list[i])
            global_constants.railtype_table[name.value] = i

    def pre_process(self):
        pass

    def debug_print(self, indentation):
        print indentation*' ' + 'Railtype table'
        for railtype in self.railtype_list:
            print (indentation+2)*' ' + 'Railtype: %s' % str(railtype.value)

    def get_action_list(self):
        return action0.get_railtypelist_action(self.railtype_list)

    def __str__(self):
        ret = 'railtypetable {\n'
        ret += ', '.join([expression.identifier_to_print(railtype.value) for railtype in self.railtype_list])
        ret += '\n}\n'
        return ret
