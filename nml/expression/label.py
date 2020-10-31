from nml import generic, grfstrings

from .base_expression import ConstantNumeric
from .string_literal import StringLiteral
from .identifier import Identifier

class Label(ConstantNumeric):
    def __init__(self, value, pos=None):
        if isinstance(value, (Identifier, StringLiteral)):
            pos = pos or value.pos
            value = value.value
        super().__init__(parse_string_to_dword(value, pos), pos)
        self.string_value = value

    def debug_print(self, indentation):
        generic.print_dbg(indentation, 'Label: "{}"'.format(self.string_value))

    def __str__(self):
        return '"{}"'.format(self.string_value)

    def write(self, file, size):
        # FIXME this is wrong with escape sequences
        # Also we should replace literal newlines with \n and so on to stop the output being messed up.
        # assert len(self.string_value) == size
        file.print_string(self.string_value, final_zero=False, force_ascii=True)



def parse_string_to_dword(string, pos):
    """
    Convert a 4-byte string to its equivalent 32 bit number.

    @param string: String to convert.
    @type  string: C{str}

    @param pos: Position of the original string in the file
    @type  pos: L{Position} or C{None}

    @return: Value of the converted expression (a 32 bit integer number, little endian).
    @rtype:  C{int}
    """

    # FIXME get_string_size is all wrong, and there must be a tidier way to solve this
    if grfstrings.get_string_size(string, final_zero=False, force_ascii=True) != 4:
        raise generic.ScriptError("Expected a string literal of length 4", pos)

    bytes = []
    i = 0
    try:
        while len(bytes) < 4:
            if string[i] == '\\':
                bytes.append(int(string[i+1:i+3], 16))
                i += 3
            else:
                bytes.append(ord(string[i]))
                i += 1
    except ValueError:
        raise generic.ScriptError("Cannot convert string to integer id", pos)

    return bytes[0] | (bytes[1] << 8) | (bytes[2] << 16) | (bytes[3] << 24)
