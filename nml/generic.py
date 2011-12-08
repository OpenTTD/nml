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

# -*- coding: utf-8 -*-
import sys

def truncate_int32(value):
    """
    Truncate the given value so it can be stored in exactly 4 bytes. The sign
    will be kept. Too high or too low values will be cut off, not clamped to
    the valid range.

    @param value: The value to truncate.
    @type value: C{int}

    @return: The truncated value.
    @rtype: C{int}.
    """
    #source: http://www.tiac.net/~sw/2010/02/PureSalsa20/index.html
    return int( (value & 0x7fffFFFF) | -(value & 0x80000000) )

def check_range(value, min_value, max_value, name, pos):
    """
    Check if a value is within a certain range and raise an error if it's not.

    @param value: The value to check.
    @type value: C{int}

    @param min_value: Minimum valid value.
    @type min_value: C{int}

    @param max_value: Maximum valid value.
    @type max_value: C{int}

    @param name: Name of the variable that is being tested.
    @type name: C{basestring}

    @param pos: Position information from the variable being tested.
    @type pos: L{Position}
    """
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
        ScriptError.__init__(self, "Expected a compile-time integer constant", pos)

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
    if pos:
        print >> sys.stderr, str(pos) + ":",

    print >> sys.stderr, msg

