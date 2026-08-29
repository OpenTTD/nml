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

from nml.ast import base_statement
from nml.expression.array import Array


class InArrayFor(base_statement.BaseStatement):
    def __init__(self, array, param, expressions, pos=None):
        base_statement.BaseStatement.__init__(self, "for", pos, False, False)
        self.array = array
        self.param = param
        self.expressions = expressions

    def __str__(self):
        expressions_string = ""
        for expression in self.expressions:
            expressions_string += str(expression) + ", "
        expressions_string = expressions_string[:-2]
        return "[{} for {} in {}]".format(
            expressions_string,
            self.param,
            self.array,
        )

    def reduce(self, id_dicts=None, unknown_id_fatal=True):
        self.array = self.array.reduce(id_dicts, unknown_id_fatal)
        out_list = []
        for value in self.array.values:
            param_tuple = ({self.param.value: value}, lambda name, x, pos: x)
            id_dicts.append(param_tuple)
            for expression in self.expressions:
                out_list.append(expression.reduce(id_dicts, unknown_id_fatal))
            id_dicts.remove(param_tuple)
        return Array(out_list, self.pos)
