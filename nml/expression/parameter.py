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

from .base_expression import ConstantNumeric, Expression, Type
from .string_literal import StringLiteral


class Parameter(Expression):
    def __init__(self, num, pos=None, by_user=False):
        Expression.__init__(self, pos)
        self.num = num
        if by_user and isinstance(num, ConstantNumeric) and not (0 <= num.value <= 63):
            generic.print_warning(
                "Accessing parameters out of the range 0..63 is not supported and may lead to unexpected behaviour.",
                pos,
            )

    def debug_print(self, indentation):
        generic.print_dbg(indentation, "Parameter:")
        self.num.debug_print(indentation + 2)

    def __str__(self):
        return "param[{}]".format(self.num)

    def reduce(self, id_dicts=None, unknown_id_fatal=True):
        num = self.num.reduce(id_dicts)
        if num.type() != Type.INTEGER:
            raise generic.ScriptError("Parameter number must be an integer.", num.pos)
        return Parameter(num, self.pos)

    def supported_by_action2(self, raise_error):
        supported = isinstance(self.num, ConstantNumeric)
        if not supported and raise_error:
            raise generic.ScriptError(
                "Parameter acessess with non-constant numbers are not supported in a switch-block.", self.pos
            )
        return supported

    def supported_by_actionD(self, raise_error):
        return True

    def __eq__(self, other):
        return other is not None and isinstance(other, Parameter) and self.num == other.num

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash((self.num,))


class OtherGRFParameter(Expression):
    def __init__(self, grfid, num, pos=None):
        Expression.__init__(self, pos)
        self.grfid = grfid
        self.num = num

    def debug_print(self, indentation):
        generic.print_dbg(indentation, "OtherGRFParameter:")
        self.grfid.debug_print(indentation + 2)
        self.num.debug_print(indentation + 2)

    def __str__(self):
        return "param[{}, {}]".format(self.grfid, self.num)

    def reduce(self, id_dicts=None, unknown_id_fatal=True):
        grfid = self.grfid.reduce(id_dicts)
        # Test validity
        parse_string_to_dword(grfid)
        num = self.num.reduce(id_dicts)
        if num.type() != Type.INTEGER:
            raise generic.ScriptError("Parameter number must be an integer.", num.pos)
        return OtherGRFParameter(grfid, num, self.pos)

    def supported_by_action2(self, raise_error):
        if raise_error:
            raise generic.ScriptError(
                "Reading parameters from another GRF is not supported in a switch-block.", self.pos
            )
        return False

    def supported_by_actionD(self, raise_error):
        return True


def parse_string_to_dword(string):
    """
    Convert string literal expression of length 4 to it's equivalent 32 bit number.

    @param string: Expression to convert.
    @type  string: L{Expression}

    @return: Value of the converted expression (a 32 bit integer number, little endian).
    @rtype:  C{int}
    """
    if not isinstance(string, StringLiteral) or grfstrings.get_string_size(string.value, False, True) != 4:
        raise generic.ScriptError("Expected a string literal of length 4", string.pos)

    pos = string.pos
    string = string.value
    bytes = []
    i = 0
    try:
        while len(bytes) < 4:
            if string[i] == "\\":
                bytes.append(int(string[i + 1 : i + 3], 16))
                i += 3
            else:
                bytes.append(ord(string[i]))
                i += 1
    except ValueError:
        raise generic.ScriptError("Cannot convert string to integer id", pos)

    return bytes[0] | (bytes[1] << 8) | (bytes[2] << 16) | (bytes[3] << 24)
