# SPDX-License-Identifier: GPL-2.0-or-later

from nml import generic

from .base_expression import Expression, Type


class Boolean(Expression):
    """
    Convert to boolean truth value.

    @ivar expr: (Integer) expression to convert.
    @type expr: C{Expression}
    """

    def __init__(self, expr, pos=None):
        Expression.__init__(self, pos)
        self.expr = expr

    def debug_print(self, indentation):
        generic.print_dbg(indentation, "Force expression to boolean:")
        self.expr.debug_print(indentation + 2)

    def reduce(self, id_dicts=None, unknown_id_fatal=True):
        expr = self.expr.reduce(id_dicts)
        if expr.type() != Type.INTEGER:
            if expr.type() == Type.SPRITEGROUP_REF:
                raise generic.ProcCallSyntaxError(expr.name, expr.pos)
            raise generic.ScriptError("Only integers can be converted to a boolean value.", expr.pos)
        if expr.is_boolean():
            return expr
        return Boolean(expr)

    def supported_by_action2(self, raise_error):
        return self.expr.supported_by_action2(raise_error)

    def supported_by_actionD(self, raise_error):
        return self.expr.supported_by_actionD(raise_error)

    def collect_references(self):
        return self.expr.collect_references()

    def is_read_only(self):
        return self.expr.is_read_only()

    def is_boolean(self):
        return True

    def __str__(self):
        return "!!({})".format(self.expr)
