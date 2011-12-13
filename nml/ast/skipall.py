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

class SkipAll(base_statement.BaseStatement):
    """
    Skip everything after this statement.
    """
    def __init__(self, pos):
        base_statement.BaseStatement.__init__(self, "exit-statement", pos)

    def get_action_list(self):
        return [action7.UnconditionalSkipAction(9, 0)]

    def debug_print(self, indentation):
        print indentation*' ' + 'Skip all'

    def __str__(self):
        return "exit;\n"
