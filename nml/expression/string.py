# SPDX-License-Identifier: GPL-2.0-or-later

from functools import reduce

from nml import generic

from .base_expression import Expression
from .identifier import Identifier


class String(Expression):
    def __init__(self, params, pos):
        Expression.__init__(self, pos)
        if len(params) == 0:
            raise generic.ScriptError("string() requires at least one parameter.", pos)
        self.name = params[0]
        if not isinstance(self.name, Identifier):
            raise generic.ScriptError("First parameter of string() must be an identifier.", pos)
        self.params = params[1:]

    def debug_print(self, indentation):
        generic.print_dbg(indentation, "String:")
        self.name.debug_print(indentation + 2)
        for param in self.params:
            generic.print_dbg(indentation + 2, "Parameter:")
            param.debug_print(indentation + 4)

    def __str__(self):
        ret = "string(" + self.name.value
        for p in self.params:
            ret += ", " + str(p)
        ret += ")"
        return ret

    def reduce(self, id_dicts=None, unknown_id_fatal=True):
        params = [p.reduce(id_dicts) for p in self.params]
        return String([self.name] + params, self.pos)

    def __eq__(self, other):
        return (
            other is not None and isinstance(other, String) and self.name == other.name and self.params == other.params
        )

    def __hash__(self):
        return hash(self.name) ^ reduce(lambda x, y: x ^ hash(y), self.params, 0)
