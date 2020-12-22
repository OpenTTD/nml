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

from .base_expression import Expression


class PatchVariable(Expression):
    """
    Class for reading so-called 'patch variables' via a special ActionD

    @ivar num: Variable number to read
    @type num: C{int}
    """

    def __init__(self, num, pos=None):
        Expression.__init__(self, pos)
        self.num = num

    def debug_print(self, indentation):
        generic.print_dbg(indentation, "PatchVariable:", self.num)

    def __str__(self):
        return "PatchVariable({:d})".format(self.num)

    def reduce(self, id_dicts=None, unknown_id_fatal=True):
        return self

    def supported_by_action2(self, raise_error):
        if raise_error:
            raise generic.ScriptError("Reading patch variables is not supported in a switch-block.", self.pos)
        return False

    def supported_by_actionD(self, raise_error):
        return True
