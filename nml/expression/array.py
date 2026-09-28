# SPDX-License-Identifier: GPL-2.0-or-later

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
