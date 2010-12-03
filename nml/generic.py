# -*- coding: utf-8 -*-
import sys

def to_hex(value, width = 0):
    ret = hex(value)[2:].upper()
    if ret[-1] == 'L': ret = ret[0:-1]
    return ret.zfill(width)

def truncate_int32(value):
    #source: http://www.tiac.net/~sw/2010/02/PureSalsa20/index.html
    return int( (value & 0x7fffFFFF) | -(value & 0x80000000) )

def check_range(value, min_value, max_value, name, pos):
    if not min_value <= value <= max_value:
        raise RangeError(value, min_value, max_value, name, pos)

def reverse_lookup(dic, val):
    #reverse dictionary lookup
    return [k for k, v in dic.iteritems() if v == val][0]

class Position(object):
    """
    Base class representing a position in a file.

    @ivar filename: Name of the file.
    @type filename: C{str}
    """
    def __init__(self, filename):
        self.filename = filename

class LinePosition(Position):
    """
    Line in a file.

    @ivar line_start: Line number (starting with 1) where the position starts.
    @type line_start: C{int}
    """
    def __init__(self, filename, line_start):
        Position.__init__(self, filename)
        self.line_start = line_start

    def __str__(self):
        return '"%s", line %d' % (self.filename, self.line_start)

class PixelPosition(Position):
    """
    Position of a pixel (in a file with graphics).

    @ivar xpos: Horizontal position of the pixel.
    @type xpos: C{int}

    @ivar ypos: Vertical position of the pixel.
    @type ypos: C{int}
    """
    def __init__(self, filename, xpos, ypos):
        Position.__init__(self, filename)
        self.xpos = xpos
        self.ypos = ypos

    def __str__(self):
        return '"%s" at [x: %d, y: %d]' % (self.filename, self.xpos, self.ypos)


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

class ImageError(ScriptError):
    def __init__(self, value, filename):
        ScriptError.__init__(self, value, 'Image file "%s"' % filename)

class OnlyOnceError(ScriptError):
    def __init__(self, typestr, pos = None):
        ScriptError.__init__(self, "A grf may contain only one %s." % typestr, pos)

class OnlyOnce:
    """
    Class to enforce that certain objects / constructs appear only once.
    """
    seen = {}

    @classmethod
    def enforce(cls, obj, typestr):
        """
        If this method is called more than once for an object of the exact same
        class, an OnlyOnceError is raised.
        """
        objtype = obj.__class__
        if objtype in cls.seen:
            raise OnlyOnceError(typestr, obj.pos)
        cls.seen[objtype] = None

    @classmethod
    def clear(cls):
        cls.seen = {}

def print_warning(msg, pos = None):
    """
    Output a warning message to the user.
    """
    if pos is None:
        text = msg
    else:
        text = str(pos) + ": " + msg

    sys.stderr.write(text)
    sys.stderr.write("\n")

