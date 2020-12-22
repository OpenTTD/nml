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

from nml import generic

from .base_expression import Expression


class Array(Expression):
    def __init__(self, values, pos):
        Expression.__init__(self, pos)
        self.values = values

    def debug_print(self, indentation):
        generic.print_dbg(indentation, "Array of values:")
        for v in self.values:
            v.debug_print(indentation + 2)

    def __str__(self):
        return "[" + ", ".join([str(expr) for expr in self.values]) + "]"

    def reduce(self, id_dicts=None, unknown_id_fatal=True):
        return Array([val.reduce(id_dicts, unknown_id_fatal) for val in self.values], self.pos)

    def collect_references(self):
        from itertools import chain

        return list(chain.from_iterable(v.collect_references() for v in self.values))

    def is_read_only(self):
        return all(v.is_read_only() for v in self.values)
