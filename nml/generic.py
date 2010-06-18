# -*- coding: utf-8 -*-

def to_hex(value, width = 0):
    ret = hex(value)[2:].upper()
    if ret[-1] == 'L': ret = ret[0:-1]
    return ret.zfill(width)

def truncate_int32(value):
    #source: http://www.tiac.net/~sw/2010/02/PureSalsa20/index.html
    return int( (value & 0x7fffFFFF) | -(value & 0x80000000) )

def check_range(value, min_value, max_value, name):
    if not min_value <= value <= max_value:
        raise RangeError(value, min_value, max_value, name)


class Position(object):
    """
    Position in a file.

    @ivar filename: Name of the file.
    @type filename: C{str}

    @ivar line_start: Line number (starting with 1) where the position starts.
    @type line_start: C{int}
    """
    def __init__(self, filename, line_start):
        self.filename = filename
        self.line_start = line_start

    def __str__(self):
        return '"%s", line %d' % (self.filename, self.line_start)


class ScriptError(Exception):
    def __init__(self, value, pos = None):
        self.value = value
        self.pos = pos

    def __str__(self):
        if self.pos is None:
            return self.value
        else:
            return str(self.pos) + ": " + self.value

class ConstError(ScriptError):
    def __init__(self, pos = None):
        ScriptError.__init__(self, "Expected a compile-time constant", pos)

class RangeError(ScriptError):
    def __init__(self, value, min_value, max_value, name, pos = None):
        ScriptError.__init__(self, name + " out of range " + str(min_value) + ".." + str(max_value) + ", encountered " + str(value), pos)
