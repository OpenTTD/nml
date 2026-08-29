# SPDX-License-Identifier: GPL-2.0-or-later

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
