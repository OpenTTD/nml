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

from nml import generic, nmlop
from .base_expression import Type, Expression, ConstantNumeric
from .binop import BinOp
from .boolean import Boolean

class BinNot(Expression):
    def __init__(self, expr, pos = None):
        Expression.__init__(self, pos)
        self.expr = expr

    def debug_print(self, indentation):
        print indentation*' ' + 'Binary not:'
        self.expr.debug_print(indentation + 2)

    def reduce(self, id_dicts = [], unknown_id_fatal = True):
        expr = self.expr.reduce(id_dicts)
        if expr.type() != Type.INTEGER:
            raise generic.ScriptError("Not-operator (~) requires an integer argument.", expr.pos)
        if isinstance(expr, ConstantNumeric): return ConstantNumeric(0xFFFFFFFF ^ expr.value)
        if isinstance(expr, BinNot): return expr.expr
        return BinNot(expr)

    def supported_by_action2(self, raise_error):
        return self.expr.supported_by_action2(raise_error)

    def supported_by_actionD(self, raise_error):
        return self.expr.supported_by_actionD(raise_error)

    def __str__(self):
        return "~" + str(self.expr)

class Not(Expression):
    def __init__(self, expr, pos = None):
        Expression.__init__(self, pos)
        self.expr = expr

    def debug_print(self, indentation):
        print indentation*' ' + 'Logical not:'
        self.expr.debug_print(indentation + 2)

    def reduce(self, id_dicts = [], unknown_id_fatal = True):
        expr = self.expr.reduce(id_dicts)
        if expr.type() != Type.INTEGER:
            raise generic.ScriptError("Not-operator (!) requires an integer argument.", expr.pos)
        if isinstance(expr, ConstantNumeric): return ConstantNumeric(expr.value != 0)
        if isinstance(expr, Not): return Boolean(expr.expr).reduce()
        if isinstance(expr, BinOp):
            if expr.op == nmlop.CMP_EQ: return BinOp(nmlop.CMP_NEQ, expr.expr1, expr.expr2)
            if expr.op == nmlop.CMP_NEQ: return BinOp(nmlop.CMP_EQ, expr.expr1, expr.expr2)
            if expr.op == nmlop.CMP_LE: return BinOp(nmlop.CMP_GT, expr.expr1, expr.expr2)
            if expr.op == nmlop.CMP_GE: return BinOp(nmlop.CMP_LT, expr.expr1, expr.expr2)
            if expr.op == nmlop.CMP_LT: return BinOp(nmlop.CMP_GE, expr.expr1, expr.expr2)
            if expr.op == nmlop.CMP_GT: return BinOp(nmlop.CMP_LE, expr.expr1, expr.expr2)
            if expr.op == nmlop.HASBIT: return BinOp(nmlop.NOTHASBIT, expr.expr1, expr.expr2)
            if expr.op == nmlop.NOTHASBIT: return BinOp(nmlop.HASBIT, expr.expr1, expr.expr2)
        return Not(expr)

    def supported_by_action2(self, raise_error):
        return self.expr.supported_by_action2(raise_error)

    def supported_by_actionD(self, raise_error):
        return self.expr.supported_by_actionD(raise_error)

    def is_boolean(self):
        return True

    def __str__(self):
        return "!" + str(self.expr)
