# SPDX-License-Identifier: GPL-2.0-or-later

from nml import generic

from .base_expression import ConstantNumeric, Expression, Type


class AbsOp(Expression):
    def __init__(self, expr, pos):
        Expression.__init__(self, pos)
        self.expr = expr

    def debug_print(self, indentation):
        generic.print_dbg(indentation, "abs():")
        self.expr.debug_print(indentation + 2)

    def reduce(self, id_dicts=None, unknown_id_fatal=True):
        expr = self.expr.reduce(id_dicts)
        if expr.type() != Type.INTEGER:
            if expr.type() == Type.SPRITEGROUP_REF:
                raise generic.ProcCallSyntaxError(expr.name, expr.pos)
            raise generic.ScriptError("abs() requires an integer argument.", expr.pos)
        if isinstance(expr, ConstantNumeric):
            if expr.value < 0:
                return ConstantNumeric(-expr.value)
            else:
                return ConstantNumeric(expr.value)
        return AbsOp(expr, self.pos)

    def supported_by_action2(self, raise_error):
        return self.expr.supported_by_action2(raise_error)

    def supported_by_actionD(self, raise_error):
        return self.expr.supported_by_actionD(raise_error)

    def collect_references(self):
        return self.expr.collect_references()

    def is_read_only(self):
        return self.expr.is_read_only()

    def __str__(self):
        return "abs(" + str(self.expr) + ")"
