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
from .base_expression import Expression, ConstantNumeric, ConstantFloat
from .string_literal import StringLiteral
from .variable import Variable
from .boolean import Boolean

class BinOp(Expression):
    def __init__(self, op, expr1, expr2, pos = None):
        Expression.__init__(self, pos)
        self.op = op
        self.expr1 = expr1
        self.expr2 = expr2

    def debug_print(self, indentation):
        print indentation*' ' + 'Binary operator, op = ', self.op.token
        self.expr1.debug_print(indentation + 2)
        self.expr2.debug_print(indentation + 2)

    def __str__(self):
        if self.op == nmlop.SUB and isinstance(self.expr1, ConstantNumeric) and self.expr1.value == 0:
            return '-' + str(self.expr2)
        return self.op.to_string(self.expr1, self.expr2)

    def get_priority(self, expr):
        """
        Get the priority of an expression. For optimalization reason we prefer complexer
        expressions (= low priority) on the left hand side of this expression. The following
        priorities are used:
        -1: everything that doesn't fit in one of the other categories.
         0: Variables to be parsed in a varaction2
         1: Expressions that can be parsed via actionD, with the exception of constant numbers
         2: constant numbers

        @param expr: The expression to get the priority of.
        @type  expr: L{Expression}

        @return: The priority for the given expression.
        @rtype: C{int}
        """
        if isinstance(expr, Variable): return 0
        if isinstance(expr, ConstantNumeric): return 2
        if expr.supported_by_actionD(False): return 1
        return -1

    def reduce(self, id_dicts = [], unknown_id_fatal = True):
        # Reducing a BinOp expression is done in several phases:
        # - Reduce both subexpressions.
        # - If both subexpressions are constant, compute the result and return it.
        # - If the operator allows it and the second expression is more complex than
        #   the first one swap them.
        # - If the operation is a no-op, delete it.
        # - Variables (as used in action2var) can have some computations attached to
        #   them, do that if possible.
        # - Try to merge multiple additions/subtractions with constant numbers

        # - Reduce both subexpressions.
        expr1 = self.expr1.reduce(id_dicts)
        expr2 = self.expr2.reduce(id_dicts)

        # Make sure the combination of operands / operator is valid
        if self.op.validate_func is not None:
            self.op.validate_func(expr1, expr2, self.pos)

        # - If both subexpressions are constant, compute the result and return it.
        if isinstance(expr1, ConstantNumeric) and isinstance(expr2, ConstantNumeric) and self.op.compiletime_func is not None:
            return ConstantNumeric(self.op.compiletime_func(expr1.value, expr2.value), self.pos)

        if isinstance(expr1, StringLiteral) and isinstance(expr2, StringLiteral):
            assert self.op == nmlop.ADD
            return StringLiteral(expr1.value + expr2.value, expr1.pos)

        if isinstance(expr1, (ConstantNumeric, ConstantFloat)) and isinstance(expr2, (ConstantNumeric, ConstantFloat)) and self.op.compiletime_func is not None:
            return ConstantFloat(self.op.compiletime_func(expr1.value, expr2.value), self.pos)

        # - If the operator allows it and the second expression is more complex than
        #   the first one swap them.
        op = self.op
        if op in commutative_operators or self.op in (nmlop.CMP_LT, nmlop.CMP_GT):
            prio1 = self.get_priority(expr1)
            prio2 = self.get_priority(expr2)
            if prio2 < prio1:
                expr1, expr2 = expr2, expr1
                if op == nmlop.CMP_LT:
                    op = nmlop.CMP_GT
                elif op == nmlop.CMP_GT:
                    op = nmlop.CMP_LT

        # - If the operation is a no-op, delete it.
        if op == nmlop.AND and isinstance(expr2, ConstantNumeric) and (expr2.value == -1 or expr2.value == 0xFFFFFFFF):
            return expr1

        if op in (nmlop.DIV, nmlop.DIVU, nmlop.MUL) and isinstance(expr2, ConstantNumeric) and expr2.value == 1:
            return expr1

        if op in (nmlop.ADD, nmlop.SUB) and isinstance(expr2, ConstantNumeric) and expr2.value == 0:
            return expr1

        # - Variables (as used in action2var) can have some computations attached to
        #   them, do that if possible.
        if isinstance(expr1, Variable) and expr2.supported_by_actionD(False):
            # An action2 Variable has some special fields (mask, add, div and mod) that can be used
            # to perform some operations on the value. These operations are faster than a normal
            # advanced varaction2 operator so we try to use them whenever we can.
            if op == nmlop.AND and expr1.add is None:
                expr1.mask = BinOp(nmlop.AND, expr1.mask, expr2, self.pos).reduce(id_dicts)
                return expr1
            if op == nmlop.ADD and expr1.div is None and expr1.mod is None:
                if expr1.add is None: expr1.add = expr2
                else: expr1.add = BinOp(nmlop.ADD, expr1.add, expr2, self.pos).reduce(id_dicts)
                return expr1
            if op == nmlop.SUB and expr1.div is None and expr1.mod is None:
                if expr1.add is None: expr1.add = ConstantNumeric(0)
                expr1.add = BinOp(nmlop.SUB, expr1.add, expr2, self.pos).reduce(id_dicts)
                return expr1
            # The div and mod fields cannot be used at the same time. Also whenever either of those
            # two are used the add field has to be set, so we change it to zero when it's not yet set.
            if op == nmlop.DIV and expr1.div is None and expr1.mod is None:
                if expr1.add is None: expr1.add = ConstantNumeric(0)
                expr1.div = expr2
                return expr1
            if op == nmlop.MOD and expr1.div is None and expr1.mod is None:
                if expr1.add is None: expr1.add = ConstantNumeric(0)
                expr1.mod = expr2
                return expr1
            # Since we have a lot of nml-variables that are in fact only the high bits of an nfo
            # variable it can happen that we want to shift back the variable to the left.
            # Don't use any extra opcodes but just reduce the shift-right in that case.
            if op == nmlop.SHIFT_LEFT and isinstance(expr2, ConstantNumeric) and expr1.add is None and expr2.value < expr1.shift.value:
                expr1.shift.value -= expr2.value
                expr1.mask = BinOp(nmlop.SHIFT_LEFT, expr1.mask, expr2).reduce()
                return expr1

        # - Try to merge multiple additions/subtractions with constant numbers
        if op in (nmlop.ADD, nmlop.SUB) and isinstance(expr2, ConstantNumeric) and \
                isinstance(expr1, BinOp) and expr1.op in (nmlop.ADD, nmlop.SUB) and isinstance(expr1.expr2, ConstantNumeric):
            val = expr2.value if op == nmlop.ADD else -expr2.value
            if expr1.op == nmlop.ADD:
                return BinOp(nmlop.ADD, expr1.expr1, ConstantNumeric(expr1.expr2.value + val), self.pos).reduce()
            if expr1.op == nmlop.SUB:
                return BinOp(nmlop.SUB, expr1.expr1, ConstantNumeric(expr1.expr2.value - val), self.pos).reduce()

        if op == nmlop.OR and isinstance(expr1, Boolean) and isinstance(expr2, Boolean):
            return Boolean(BinOp(op, expr1.expr, expr2.expr, self.pos)).reduce(id_dicts)

        return BinOp(op, expr1, expr2, self.pos)

    def supported_by_action2(self, raise_error):
        if not self.op.act2_supports:
            token = " '%s'" % self.op.token if self.op.token else ""
            if raise_error: raise generic.ScriptError("Operator%s not supported in a switch-block" % token, self.pos)
            return False
        return self.expr1.supported_by_action2(raise_error) and self.expr2.supported_by_action2(raise_error)

    def supported_by_actionD(self, raise_error):
        if not self.op.actd_supports:
            token = " '%s'" % self.op.token if self.op.token else ""
            if raise_error:
                if self.op == nmlop.STO_PERM: raise generic.ScriptError("STORE_PERM is only available in switch-blocks.", self.pos)
                elif self.op == nmlop.STO_TMP: raise generic.ScriptError("STORE_TEMP is only available in switch-blocks.", self.pos)
                #default case
                raise generic.ScriptError("Operator%s not supported in parameter assignment" % token, self.pos)
            return False
        return self.expr1.supported_by_actionD(raise_error) and self.expr2.supported_by_actionD(raise_error)

    def is_boolean(self):
        if self.op in (nmlop.AND, nmlop.OR, nmlop.XOR):
            return self.expr1.is_boolean() and self.expr2.is_boolean()
        return self.op.returns_boolean

    def __eq__(self, other):
        return other is not None and isinstance(other, BinOp) and self.op == other.op and self.expr1 == other.expr1 and self.expr2 == other.expr2

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash((self.op, self.expr1, self.expr2))

commutative_operators = set([
    nmlop.ADD,
    nmlop.MUL,
    nmlop.AND,
    nmlop.OR,
    nmlop.XOR,
    nmlop.CMP_EQ,
    nmlop.CMP_NEQ,
    nmlop.MIN,
    nmlop.MAX,
])
