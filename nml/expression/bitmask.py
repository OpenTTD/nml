# SPDX-License-Identifier: GPL-2.0-or-later

from nml import generic, nmlop

from .base_expression import ConstantNumeric, Expression, Type


class BitMask(Expression):
    def __init__(self, values, pos):
        Expression.__init__(self, pos)
        self.values = values

    def debug_print(self, indentation):
        generic.print_dbg(indentation, "Get bitmask:")
        for value in self.values:
            value.debug_print(indentation + 2)

    def reduce(self, id_dicts=None, unknown_id_fatal=True):
        ret = ConstantNumeric(0, self.pos)
        for orig_expr in self.values:
            val = orig_expr.reduce(id_dicts)
            if val.type() != Type.INTEGER:
                if val.type() == Type.SPRITEGROUP_REF:
                    raise generic.ProcCallSyntaxError(val.name, val.pos)
                raise generic.ScriptError("Parameters of 'bitmask' must be integers.", orig_expr.pos)
            if isinstance(val, ConstantNumeric) and val.value >= 32:
                raise generic.ScriptError("Parameters of 'bitmask' cannot be greater than 31", orig_expr.pos)
            val = nmlop.SHIFT_LEFT(1, val)
            ret = nmlop.OR(ret, val)
        return ret.reduce()

    def collect_references(self):
        from itertools import chain

        return list(chain.from_iterable(v.collect_references() for v in self.values))

    def is_read_only(self):
        return all(v.is_read_only() for v in self.values)

    def __str__(self):
        return "bitmask(" + ", ".join(str(e) for e in self.values) + ")"
