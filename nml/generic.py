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
import sys, os

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

def greatest_common_divisor(a, b):
    """
    Get the greatest common divisor of two numbers
    """
    while b != 0:
        t = b
        b = a % b
        a = t
    return a

def reverse_lookup(dic, val):
    #reverse dictionary lookup
    return [k for k, v in dic.iteritems() if v == val][0]

class Position(object):
    """
    Base class representing a position in a file.

    @ivar filename: Name of the file.
    @type filename: C{str}

    @ivar includes: List of file includes
    @type includes: C{list} of L{Position}
    """
    def __init__(self, filename, includes):
        self.filename = filename
        self.includes = includes

class LinePosition(Position):
    """
    Line in a file.

    @ivar line_start: Line number (starting with 1) where the position starts.
    @type line_start: C{int}
    """
    def __init__(self, filename, line_start, includes = []):
        Position.__init__(self, filename, includes)
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
        Position.__init__(self, filename, [])
        self.xpos = xpos
        self.ypos = ypos

    def __str__(self):
        return '"%s" at [x: %d, y: %d]' % (self.filename, self.xpos, self.ypos)

class ImageFilePosition(Position):
    """
    Generic (not position-dependant) error with an image file
    """
    def __init__(self, filename):
        Position.__init__(self, filename, [])

    def __str__(self):
        return 'Image file "%s"' % self.filename

class LanguageFilePosition(Position):
    """
    Generic (not position-dependant) error with a language file.
    """
    def __init__(self, filename):
        Position.__init__(self, filename, [])

    def __str__(self):
        return 'Language file "%s"' % self.filename

class ScriptError(Exception):
    def __init__(self, value, pos = None):
        self.value = value
        self.pos = pos

    def __str__(self):
        if self.pos is None:
            return self.value
        else:
            ret = str(self.pos) + ": " + self.value
            for inc in reversed(self.pos.includes):
                ret += "\nIncluded from: " + str(inc)
            return ret

class ConstError(ScriptError):
    def __init__(self, pos = None):
        ScriptError.__init__(self, "Expected a compile-time integer constant", pos)

class RangeError(ScriptError):
    def __init__(self, value, min_value, max_value, name, pos = None):
        ScriptError.__init__(self, name + " out of range " + str(min_value) + ".." + str(max_value) + ", encountered " + str(value), pos)

class ImageError(ScriptError):
    def __init__(self, value, filename):
        ScriptError.__init__(self, value, ImageFilePosition(filename))

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

do_print_warnings = True

def disable_warnings():
    global do_print_warnings
    do_print_warnings = False

def print_warning(msg, pos = None):
    """
    Output a warning message to the user.
    """
    if not do_print_warnings:
        return
    if pos:
        msg = str(pos) + ": " + msg

    print >> sys.stderr, "nmlc warning: " + msg

def print_error(msg):
    """
    Output an error message to the user.
    """
    print >> sys.stderr, "nmlc ERROR: " + msg

_paths = set() # Paths already found to be correct at the system.

def find_file(path):
    """
    Verify whether L{path} exists. If not, try to find a similar one with a
    different case.

    @param path: Path to the file to open.
    @type  path: C{str}

    @return: Path name to a file that exists at the file system.
    @rtype:  C{str}
    """
    # Split the path in components (directory parts and the filename).
    drive, path = os.path.splitdrive(os.path.normpath(path))
    components = [] # Path stored in reverse order (filename at index[0])
    while path != '':
        dirpart, filepart = os.path.split(path)
        components.append(filepart)
        path = dirpart

    # Re-build the path
    path = drive
    while len(components) > 0:
        comp = components.pop()
        newpath = os.path.join(path, comp)
        if newpath in _paths:
            path = newpath
            continue

        lcomp = comp.lower()
        if path == '':
            entries = os.listdir(os.curdir) + [os.curdir, os.pardir]
        else:
            entries = os.listdir(path) + [os.curdir, os.pardir]
        matches = [entry for entry in entries if lcomp == entry.lower()]
        if len(matches) == 0:
            raise ScriptError("Path \"%s\" does not exist (even after case conversions)" % os.path.join(path, comp))
        elif len(matches) > 1:
            raise ScriptError("Path \"%s\" is not unique (case conversion gave %d solutions)" % (os.path.join(path, comp), len(matches)))

        if matches[0] != comp:
            given_path = os.path.join(path, comp)
            real_path = os.path.join(path, matches[0])
            print_warning("Path \"%s\" at the file system does not match path \"%s\" given in the input (case mismatch in the last component)"
                    % (real_path, given_path))

        path = os.path.join(path, matches[0])
        if len(components) > 0:
            _paths.add(path)

    return path
