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
from nml.ast import base_statement, general
from nml.actions import action0

class SortVehicles(base_statement.BaseStatement):
    """
    AST-node representing a sort-vehicles block.
    @ivar feature: Feature of the item
    @type feature: L{ConstantNumeric}

    @ivar vehid_list: List of vehicle ids.
    @type vehid_list: L{Array}.
    """
    def __init__(self, params, pos):
        base_statement.BaseStatement.__init__(self, "sort-block", pos)
        if len(params) != 2:
            raise generic.ScriptError("Sort-block requires exactly two parameters, got %d" % len(params), self.pos)
        self.feature = general.parse_feature(params[0])
        self.vehid_list = params[1]

    def pre_process(self):
        self.vehid_list = self.vehid_list.reduce(global_constants.const_list)
        if not isinstance(self.vehid_list, expression.Array) or not all([isinstance(x, expression.ConstantNumeric) for x in self.vehid_list.values]):
            raise generic.ScriptError("Second parameter is not an array of one of the items in it could not be reduced to a constnat numer", self.pos)

    def debug_print(self, indentation):
        print indentation*' ' + 'Sort, feature', hex(self.feature.value)
        for id in self.vehid_list.values:
            print (indentation+2)*' ' + 'Vehicle id:', id

    def get_action_list(self):
        return action0.parse_sort_block(self.feature.value, self.vehid_list.values)

    def __str__(self):
        return 'sort(%d, %s);\n' % (self.feature.value, self.vehid_list)
