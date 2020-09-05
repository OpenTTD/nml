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

from nml.actions import actionC
from nml.ast import base_statement
from nml import expression, generic

class Comment(base_statement.BaseStatement):
    def __init__(self, text, pos):
        base_statement.BaseStatement.__init__(self, "comment()", pos)
        self.text = text

    def pre_process(self):
        self.text = self.text.reduce()
        if not isinstance(self.text, expression.StringLiteral):
            raise generic.ScriptError("Comment must be a string literal.", self.text.pos)

    def debug_print(self, indentation):
        generic.print_dbg(indentation, 'Comment:')
        self.text.debug_print(indentation + 2)

    def get_action_list(self):
        return actionC.parse_actionC(self)

    def __str__(self):
        return 'comment(%s);\n' % (self.text,)
