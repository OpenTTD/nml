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

import os
import sys
import time

# Enable VT100 sequences on windows consoles
if os.name == "nt":

    class Break(Exception):
        pass

    try:
        from ctypes import byref, windll
        from ctypes.wintypes import DWORD, HANDLE

        kernel32 = windll.kernel32
        h = kernel32.GetStdHandle(-11)  # stdout
        if h is None or h == HANDLE(-1):
            raise Break()
        FILE_TYPE_CHAR = 0x0002
        if (kernel32.GetFileType(h) & 3) != FILE_TYPE_CHAR:
            raise Break()
        mode = DWORD()
        kernel32.GetConsoleMode(h, byref(mode))
        ENABLE_VIRTUAL_TERMINAL_PROCESSING = 0x0004
        if (mode.value & ENABLE_VIRTUAL_TERMINAL_PROCESSING) == 0:
            kernel32.SetConsoleMode(h, mode.value | ENABLE_VIRTUAL_TERMINAL_PROCESSING)
    except Break:
        # Early exit
        pass


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
    # source: http://www.tiac.net/~sw/2010/02/PureSalsa20/index.html
    return int((value & 0x7FFFFFFF) | -(value & 0x80000000))


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
    @type name: C{str}

    @param pos: Position information from the variable being tested.
    @type pos: L{Position}
    """
    if not min_value <= value <= max_value:
        raise RangeError(value, min_value, max_value, name, pos)


def greatest_common_divisor(a, b):
    """
    Get the greatest common divisor of two numbers

    @param a: First number.
    @type  a: C{int}

    @param b: Second number.
    @type  b: C{int}

    @return: Greatest common divisor.
    @rtype:  C{int}
    """
    while b != 0:
        t = b
        b = a % b
        a = t
    return a


def reverse_lookup(dic, val):
    """
    Perform reverse lookup of any key that has the provided value.

    @param dic: Dictionary to perform reverse lookup on.
    @type  dic: C{dict}

    @param val: Value being searched.
    @type  val: an existing value.

    @return: A key such that C{dict[key] == val}.
    @rtype:  Type of the matching key.
    """
    for k, v in dic.items():
        if v == val:
            return k
    raise AssertionError("Value not found in the dictionary.")


def build_position(poslist):
    """
    Construct a L{Position} object that takes the other positions as include list.

    @param poslist: Sequence of positions to report. First entry is the innermost position,
                    last entry is the nml statement that started it all.
    @type  poslist: C{list} of L{Position}

    @return: Position to attach to an error.
    @rtype:  L{Position}
    """
    if poslist is None or len(poslist) == 0:
        return None
    if len(poslist) == 1:
        return poslist[0]
    pos = poslist[-1]
    pos.includes = pos.includes + poslist[:-1]
    return pos


class Position:
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

    def __init__(self, filename, line_start, includes=None):
        Position.__init__(self, filename, includes or [])
        self.line_start = line_start

    def __str__(self):
        return '"{}", line {:d}'.format(self.filename, self.line_start)


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
        return '"{}" at [x: {:d}, y: {:d}]'.format(self.filename, self.xpos, self.ypos)


class ImageFilePosition(Position):
    """
    Generic (not position-dependant) error with an image file
    """

    def __init__(self, filename, pos=None):
        poslist = []
        if pos is not None:
            poslist.append(pos)
        Position.__init__(self, filename, poslist)

    def __str__(self):
        return 'Image file "{}"'.format(self.filename)


class LanguageFilePosition(Position):
    """
    Generic (not position-dependant) error with a language file.
    """

    def __init__(self, filename):
        Position.__init__(self, filename, [])

    def __str__(self):
        return 'Language file "{}"'.format(self.filename)


class ScriptError(Exception):
    def __init__(self, value, pos=None):
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
    """
    Error to denote a compile-time integer constant was expected but not found.
    """

    def __init__(self, pos=None):
        ScriptError.__init__(self, "Expected a compile-time integer constant", pos)


class RangeError(ScriptError):
    def __init__(self, value, min_value, max_value, name, pos=None):
        ScriptError.__init__(
            self, name + " out of range " + str(min_value) + ".." + str(max_value) + ", encountered " + str(value), pos
        )


class ProcCallSyntaxError(ScriptError):
    def __init__(self, name, pos=None):
        ScriptError.__init__(self, "Missing '()' after '{}'.".format(name), pos)


class ImageError(ScriptError):
    def __init__(self, value, filename, pos=None):
        ScriptError.__init__(self, value, ImageFilePosition(filename, pos))


class OnlyOnceError(ScriptError):
    """
    An error denoting two elements in a single grf were found, where only one is allowed.
    """

    def __init__(self, typestr, pos=None):
        """
        @param typestr: Description of the type of element encountered.
        @type  typestr: C{str}

        @param pos: Position of the error, if provided.
        @type  pos: C{None} or L{Position}
        """
        ScriptError.__init__(self, "A grf may contain only one {}.".format(typestr), pos)


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


class Warning:
    GENERIC = 0
    DEPRECATION = 1
    OPTIMISATION = 2
    disabled = None


VERBOSITY_WARNING = 1  # Verbosity level for warnings
VERBOSITY_INFO = 2  # Verbosity level for info messages
VERBOSITY_PROGRESS = 3  # Verbosity level for progress feedback
VERBOSITY_TIMING = 4  # Verbosity level for timing information

VERBOSITY_MAX = 4  # Maximum verbosity level

"""
Verbosity level for console output.
"""
verbosity_level = VERBOSITY_PROGRESS


def set_verbosity(level):
    global verbosity_level
    verbosity_level = level


def print_eol(msg):
    """
    Clear current line and print message without linefeed.
    """
    if not os.isatty(sys.stdout.fileno()):
        return

    print("\r" + msg + "\033[K", end="")


"""
Current progress message.
"""
progress_message = None

"""
Timestamp when the current processing step started.
"""
progress_start_time = None

"""
Timestamp of the last incremental progress update.
"""
progress_update_time = None


def hide_progress():
    if progress_message is not None:
        print_eol("")


def show_progress():
    if progress_message is not None:
        print_eol(progress_message)


def clear_progress():
    global progress_message
    global progress_start_time
    global progress_update_time
    hide_progress()

    if (progress_message is not None) and (verbosity_level >= VERBOSITY_TIMING):
        print("{} {:.1f} s".format(progress_message, time.process_time() - progress_start_time))

    progress_message = None
    progress_start_time = None
    progress_update_time = None


def print_progress(msg, incremental=False):
    """
    Output progess information to the user.

    @param msg: Progress message.
    @type  msg: C{str}

    @param incremental: True if this message is updated incrementally (that is, very often).
    @type  incremental: C{bool}
    """
    if verbosity_level < VERBOSITY_PROGRESS:
        return

    global progress_message
    global progress_start_time
    global progress_update_time

    if (not incremental) and (progress_message is not None):
        clear_progress()

    progress_message = msg

    if incremental:
        t = time.process_time()
        if (progress_update_time is not None) and (t - progress_update_time < 1):
            return
        progress_update_time = t
    else:
        progress_start_time = time.process_time()

    print_eol(msg)


def print_info(msg):
    """
    Output a pure informational message to th euser.
    """
    if verbosity_level < VERBOSITY_INFO:
        return

    hide_progress()
    print(" nmlc info: " + msg)
    show_progress()


def print_warning(type, msg, pos=None):
    """
    Output a warning message to the user.
    """
    if verbosity_level < VERBOSITY_WARNING:
        return
    if Warning.disabled and type in Warning.disabled:
        return
    if pos:
        msg = str(pos) + ": " + msg

    msg = " nmlc warning: " + msg

    if sys.stderr.isatty():
        msg = "\033[93m" + msg + "\033[0m"

    hide_progress()
    print(msg, file=sys.stderr)
    show_progress()


def print_error(msg, pos=None):
    """
    Output an error message to the user.
    """
    if pos:
        msg = str(pos) + ": " + msg
    else:
        clear_progress()

    msg = " nmlc ERROR: " + msg

    if sys.stderr.isatty():
        msg = "\033[91m" + msg + "\033[0m"

    hide_progress()
    print(msg, file=sys.stderr)
    show_progress()


def print_dbg(indent, *args):
    """
    Output debug text.

    @param indent: Indentation to add to the output.
    @type  indent: C{int}

    @param args: Arguments to print. An additional space is printed between them.
    @type  args: C{Tuple} of C{str}
    """
    hide_progress()
    print(indent * " " + " ".join(str(arg) for arg in args))
    show_progress()


"""
Paths already resolved to correct paths on the system.
The key is the path as specified in the sources. The value is the validated path on the system.
"""
_paths = {}


def find_file(filepath):
    """
    Verify whether L{filepath} exists. If not, try to find a similar one with a
    different case.

    @param filepath: Path to the file to open.
    @type  filepath: C{str}

    @return: Path name to a file that exists at the file system.
    @rtype:  C{str}
    """
    # Split the filepath in components (directory parts and the filename).
    drive, filepath = os.path.splitdrive(os.path.normpath(filepath))
    # 'splitdrive' above does not remove the leading / of absolute Unix paths.
    # The 'split' below splits on os.sep, which means that loop below fails for "/".
    # To prevent that, handle the leading os.sep separately.
    if filepath.startswith(os.sep):
        drive = drive + os.sep
        filepath = filepath[len(os.sep) :]

    components = []  # Path stored in reverse order (filename at index[0])
    while filepath != "":
        filepath, filepart = os.path.split(filepath)
        components.append(filepart)

    # Re-build the absolute path.
    path = drive
    if path == "":
        path = os.getcwd()
    while len(components) > 0:
        comp = components.pop()
        childpath = os.path.join(path, comp)
        if childpath in _paths:
            path = _paths[childpath]
            continue

        if os.access(path, os.R_OK):
            # Path is readable, compare provided path with the file system.
            entries = os.listdir(path) + [os.curdir, os.pardir]
            lcomp = comp.lower()
            matches = [entry for entry in entries if lcomp == entry.lower()]

            if len(matches) == 0:
                raise ScriptError(
                    'Path "{}" does not exist (even after case conversions)'.format(os.path.join(path, comp))
                )
            elif len(matches) > 1:
                raise ScriptError(
                    'Path "{}" is not unique (case conversion gave {:d} solutions)'.format(
                        os.path.join(path, comp), len(matches)
                    )
                )

            if matches[0] != comp:
                given_path = os.path.join(path, comp)
                real_path = os.path.join(path, matches[0])
                msg = (
                    'Path "{}" at the file system does not match path "{}" given in the input'
                    " (case mismatch in the last component)"
                ).format(real_path, given_path)
                print_warning(Warning.GENERIC, msg)
        elif os.access(path, os.X_OK):
            # Path is only accessible, cannot inspect the file system.
            matches = [comp]
        else:
            raise ScriptError('Path "{}" does not exist or is not accessible'.format(path))

        path = os.path.join(path, matches[0])
        if len(components) > 0:
            _paths[childpath] = path

    return path


cache_root_dir = ".nmlcache"


def set_cache_root_dir(dir):
    global cache_root_dir
    cache_root_dir = None if dir is None else os.path.abspath(dir)


def _cache_file_path(sources, extension):
    """
    Compose a filename for a cache file.

    @param sources: List of source files, the cache file depends on / belongs to.
    @type  sources: C{list} or C{tuple} of C{str} or similar.

    @param extension: File extension for the cache file including leading ".".
    @type  extension: C{str}

    @return: Filename for cache file.
    @rtype:  C{str}
    """
    result = ""

    for part in sources:
        if part is not None:
            path, name = os.path.split(part)

            if len(result) == 0:
                # Make sure that the path does not leave the cache dir
                path = os.path.normpath(path).replace(os.path.pardir, "__")
                path = os.path.join(cache_root_dir, path)
                result = os.path.join(path, name)
            else:
                # In case of multiple soure files, ignore the path component for all but the first
                result += "_" + name

    return result + extension


def open_cache_file(sources, extension, mode):
    if cache_root_dir is None:
        raise FileNotFoundError("No cache directory")

    if not any(sources):
        raise FileNotFoundError("Can't create cache file with no sources")

    path = _cache_file_path(sources, extension)

    try:
        if "w" in mode:
            os.makedirs(os.path.dirname(path), exist_ok=True)
        return open(path, mode)
    except OSError:
        if "w" in mode:
            print_warning(
                Warning.GENERIC,
                "Can't create cache file {}. Check permissions, or use --cache-dir or --no-cache.".format(path),
            )
        raise
