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

from nml import generic, grfstrings

from .base_expression import Expression, Type


class StringLiteral(Expression):
    """
    String literal expression.

    @ivar value: Value of the string literal.
    @type value: C{str}
    """

    def __init__(self, value, pos):
        Expression.__init__(self, pos)
        self.value = value

    def debug_print(self, indentation):
        generic.print_dbg(indentation, 'String literal: "{}"'.format(self.value))

    def __str__(self):
        return '"{}"'.format(self.value)

    def write(self, file, size):
        assert grfstrings.get_string_size(self.value, False, True) == size
        file.print_string(self.value, final_zero=False, force_ascii=True)

    def reduce(self, id_dicts=None, unknown_id_fatal=True):
        return self

    def type(self):
        return Type.STRING_LITERAL
