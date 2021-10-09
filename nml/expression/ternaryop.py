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

from .base_expression import ConstantNumeric, Expression, Type


class TernaryOp(Expression):
    def __init__(self, guard, expr1, expr2, pos):
        Expression.__init__(self, pos)
        self.guard = guard
        self.expr1 = expr1
        self.expr2 = expr2

    def debug_print(self, indentation):
        generic.print_dbg(indentation, "Ternary operator")
        generic.print_dbg(indentation, "Guard:")
        self.guard.debug_print(indentation + 2)
        generic.print_dbg(indentation, "Expression 1:")
        self.expr1.debug_print(indentation + 2)
        generic.print_dbg(indentation, "Expression 2:")
        self.expr2.debug_print(indentation + 2)

    def reduce(self, id_dicts=None, unknown_id_fatal=True):
        guard = self.guard.reduce(id_dicts)
        expr1 = self.expr1.reduce(id_dicts)
        expr2 = self.expr2.reduce(id_dicts)
        if isinstance(guard, ConstantNumeric):
            if guard.value != 0:
                return expr1
            else:
                return expr2
        if guard.type() != Type.INTEGER or expr1.type() != Type.INTEGER or expr2.type() != Type.INTEGER:
            raise generic.ScriptError("All parts of the ternary operator (?:) must be integers.", self.pos)
        return TernaryOp(guard, expr1, expr2, self.pos)

    def supported_by_action2(self, raise_error):
        return (
            self.guard.supported_by_action2(raise_error)
            and self.expr1.supported_by_action2(raise_error)
            and self.expr2.supported_by_action2(raise_error)
        )

    def supported_by_actionD(self, raise_error):
        return (
            self.guard.supported_by_actionD(raise_error)
            and self.expr1.supported_by_actionD(raise_error)
            and self.expr2.supported_by_actionD(raise_error)
        )

    def collect_references(self):
        return self.guard.collect_references() + self.expr1.collect_references() + self.expr2.collect_references()

    def is_read_only(self):
        return self.guard.is_read_only() and self.expr1.is_read_only() and self.expr2.is_read_only()

    def is_boolean(self):
        return self.expr1.is_boolean() and self.expr2.is_boolean()

    def __eq__(self, other):
        return (
            other is not None
            and isinstance(other, TernaryOp)
            and self.guard == other.guard
            and self.expr1 == other.expr1
            and self.expr2 == other.expr2
        )

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash((self.guard, self.expr1, self.expr2))

    def __str__(self):
        return "({} ? {} : {})".format(str(self.guard), str(self.expr1), str(self.expr2))
