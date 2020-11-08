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
from nml.actions import actionE
from nml.ast import base_statement


class DeactivateBlock(base_statement.BaseStatement):
    def __init__(self, grfid_list, pos):
        base_statement.BaseStatement.__init__(self, "deactivate()", pos)
        self.grfid_list = grfid_list

    def pre_process(self):
        # Parse (string-)expressions to integers
        self.grfid_list = [expression.parse_string_to_dword(grfid.reduce()) for grfid in self.grfid_list]

    def debug_print(self, indentation):
        generic.print_dbg(indentation, "Deactivate other newgrfs:")
        for grfid in self.grfid_list:
            grfid.debug_print(indentation + 2)

    def get_action_list(self):
        return actionE.parse_deactivate_block(self)

    def __str__(self):
        return "deactivate({});\n".format(", ".join(str(grfid) for grfid in self.grfid_list))
