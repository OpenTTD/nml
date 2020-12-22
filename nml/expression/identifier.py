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

from nml import generic, global_constants

from .base_expression import ConstantNumeric, Expression
from .string_literal import StringLiteral

ignore_all_invalid_ids = False


def default_id_func(name, x, pos):
    """
    Default id conversion function.

    @param name: Key in the containing dictionary.
    @type  name: Any, unused (to match other id_dicts callbacks)

    @param x: Value to convert.
    @type  x: C{str}, C{int}, or C{float}

    @param pos: Position of the id.
    @type  pos: L{Position}

    @return: Expression of the id.
    @rtype:  L{Expression}
    """
    del name  # unused
    if isinstance(x, str):
        return StringLiteral(x, pos)
    else:
        return ConstantNumeric(x, pos)


class Identifier(Expression):
    def __init__(self, value, pos=None):
        Expression.__init__(self, pos)
        self.value = value
        if value in global_constants.identifier_refcount:
            global_constants.identifier_refcount[value] += 1
        else:
            global_constants.identifier_refcount[value] = 0

    def debug_print(self, indentation):
        generic.print_dbg(indentation, "ID:", self.value)

    def __str__(self):
        return self.value

    def reduce(self, id_dicts=None, unknown_id_fatal=True, search_func_ptr=False):
        for id_dict in id_dicts or []:
            if isinstance(id_dict, tuple):
                id_d, func = id_dict
            else:
                id_d, func = id_dict, default_id_func

            if self.value in id_d:
                if search_func_ptr:
                    # Do not reduce function pointers, since they have no (numerical) value
                    return func(self.value, id_d[self.value], self.pos)
                else:
                    return func(self.value, id_d[self.value], self.pos).reduce(id_dicts)

        if unknown_id_fatal and not ignore_all_invalid_ids:
            raise generic.ScriptError("Unrecognized identifier '" + self.value + "' encountered", self.pos)

        return self

    def supported_by_actionD(self, raise_error):
        if raise_error:
            raise generic.ScriptError("Unknown identifier '{}'".format(self.value), self.pos)

        return False

    def __eq__(self, other):
        return other is not None and isinstance(other, Identifier) and self.value == other.value

    def __hash__(self):
        return hash(self.value)
