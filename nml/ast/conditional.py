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
from nml.actions import action7
from nml.ast import base_statement


class ConditionalList(base_statement.BaseStatementList):
    """
    Wrapper for a complete if/else if/else if/else block.
    """

    def __init__(self, conditionals):
        assert len(conditionals) > 0
        base_statement.BaseStatementList.__init__(
            self,
            "if/else-block",
            conditionals[0].pos,
            base_statement.BaseStatementList.LIST_TYPE_SKIP,
            conditionals,
            in_item=True,
        )

    def get_action_list(self):
        return action7.parse_conditional_block(self)

    def debug_print(self, indentation):
        generic.print_dbg(indentation, "Conditional")
        base_statement.BaseStatementList.debug_print(self, indentation + 2)

    def __str__(self):
        ret = ""
        ret += " else ".join([str(stmt) for stmt in self.statements])
        ret += "\n"
        return ret


class Conditional(base_statement.BaseStatementList):
    """
    Condition along with the code that has to be executed if the condition
    evaluates to some value not equal to 0.

    @ivar expr: The expression where the execution of code in this block depends on.
    @type expr: L{Expression}
    """

    def __init__(self, expr, block, pos):
        base_statement.BaseStatementList.__init__(
            self, "if/else-block", pos, base_statement.BaseStatementList.LIST_TYPE_SKIP, block, in_item=True
        )
        self.expr = expr

    def pre_process(self):
        if self.expr is not None:
            self.expr = self.expr.reduce(global_constants.const_list)
        base_statement.BaseStatementList.pre_process(self)

    def debug_print(self, indentation):
        if self.expr is not None:
            generic.print_dbg(indentation, "Expression:")
            self.expr.debug_print(indentation + 2)

        generic.print_dbg(indentation, "Block:")
        base_statement.BaseStatementList.debug_print(self, indentation + 2)

    def __str__(self):
        ret = ""
        if self.expr is not None:
            ret += "if ({})".format(self.expr)
        ret += " {\n"
        ret += base_statement.BaseStatementList.__str__(self)
        ret += "}\n"
        return ret
