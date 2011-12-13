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

from nml.actions import action7
from nml.ast import base_statement
from nml import global_constants

class Loop(base_statement.BaseStatementList):
    """
    AST node for a while-loop.

    @ivar expr: The conditional to check whether the loop continues.
    @type expr: L{Expression}
    """
    def __init__(self, expr, block, pos):
        base_statement.BaseStatementList.__init__(self, "while-loop", pos,
                base_statement.BaseStatementList.LIST_TYPE_LOOP, block, in_item = True)
        self.expr = expr

    def pre_process(self):
        self.expr = self.expr.reduce(global_constants.const_list)
        base_statement.BaseStatementList.pre_process(self)

    def debug_print(self, indentation):
        print indentation*' ' + 'While loop'
        print (2+indentation)*' ' + 'Expression:'
        self.expr.debug_print(indentation + 4)
        print (2+indentation)*' ' + 'Block:'
        base_statement.BaseStatementList.debug_print(self, indentation + 4)

    def get_action_list(self):
        return action7.parse_loop_block(self)

    def __str__(self):
        ret = 'while(%s) {\n' % self.expr
        ret += base_statement.BaseStatementList.__str__(self)
        ret += '}\n'
        return ret
