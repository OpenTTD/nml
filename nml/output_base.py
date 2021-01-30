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

"""
Abstract base classes that implements common functionality for output classes
"""
import array
import io


class OutputBase:
    """
    Base class for output to a data file.

    The file is opened with L{open}. Once that is done, data can be written
    using the L{file} data member. When finished writing, the file should be
    closed with L{close}.

    Derived classes should implement L{open_file} to perform the actual opening
    of the file. L{assemble_file} is called to actually compose the output from
    possible multiple sources.

    @ivar filename: Name of the data file.
    @type filename: C{str}

    @ivar file: Memory output file handle, if opened.
    @type file: C{file} or C{None}
    """

    def __init__(self, filename):
        self.filename = filename
        self.file = None

    def open(self):
        """
        Open the output file. Data gets stored in-memory.
        """
        raise NotImplementedError("Implement me in {}".format(type(self)))

    def open_file(self):
        """
        Construct the file handle of the disk output file.

        @return: File handle of the opened file.
        @rtype: C{file}
        """
        raise NotImplementedError("Implement me in {}".format(type(self)))

    def assemble_file(self, real_file):
        """
        File is about to be closed, last chance to append data.

        @param real_file: Actual output stream.
        @type  real_file: C{io.IOBase}
        """
        real_file.write(self.file.getvalue())

    def discard(self):
        """
        Close the memory file, without writing to disk.
        """
        if isinstance(self.file, io.IOBase):
            self.file.close()
        self.file = None

    def close(self):
        """
        Close the memory file, copy collected output to the real file.
        """
        with self.open_file() as real_file:
            self.assemble_file(real_file)
        self.discard()

    def skip_sprite_checks(self):
        """
        Return whether sprites need detailed parsing.
        """
        return False

    def __enter__(self):
        """
        Allow `OutputBase` and subclasses to be used as context managers.
        """
        self.open()
        return self

    def __exit__(self, type, value, traceback):
        """
        Allow `OutputBase` and subclasses to be used as context managers.
        """
        self.close()


class SpriteOutputBase(OutputBase):
    """
    Base class for output to a sprite file.

    @ivar in_sprite: Set to true if we are currently outputting a sprite.
                        Outputting anything when not in a sprite causes an assert.
    @type in_sprite: C{bool}

    @ivar byte_count: Number of bytes written in the current sprite.
    @type byte_count: C{int}

    @ivar expected_count: Number of bytes expected in the current sprite.
    @type expected_count: C{int}
    """

    def __init__(self, filename):
        OutputBase.__init__(self, filename)
        self.in_sprite = False
        self.expected_count = 0
        self.byte_count = 0

    def close(self):
        assert not self.in_sprite
        OutputBase.close(self)

    def prepare_byte(self, value):
        """
        Normalize the provided value to an unsigned byte value.

        @param value: Value to normalize.
        @type  value: C{int}

        @return: Normalized value (0..255).
        @rtype:  C{int}

        @precond: Must be outputting a sprite.
        """
        assert self.in_sprite
        if -0x80 <= value < 0:
            value += 0x100
        assert value >= 0 and value <= 0xFF
        self.byte_count += 1
        return value

    def prepare_word(self, value):
        """
        Normalize the provided value to an unsigned word value.

        @param value: Value to normalize.
        @type  value: C{int}

        @return: Normalized value (0..65535).
        @rtype:  C{int}

        @precond: Must be outputting a sprite.
        """
        assert self.in_sprite
        if -0x8000 <= value < 0:
            value += 0x10000
        assert value >= 0 and value <= 0xFFFF
        self.byte_count += 2
        return value

    def prepare_dword(self, value):
        """
        Normalize the provided value to an unsigned double word value.

        @param value: Value to normalize.
        @type  value: C{int}

        @return: Normalized value (0..0xFFFFFFFF).
        @rtype:  C{int}

        @precond: Must be outputting a sprite.
        """
        assert self.in_sprite
        if -0x80000000 <= value < 0:
            value += 0x100000000
        assert value >= 0 and value <= 0xFFFFFFFF
        self.byte_count += 4
        return value

    def print_varx(self, value, size):
        """
        Print a variable sized value.

        @param value: Value to output.
        @type  value: C{int}

        @param size: Size of the output (1..4), 3 means extended byte.
        @type  size: C{int}
        """
        if size == 1:
            self.print_bytex(value)
        elif size == 2:
            self.print_wordx(value)
        elif size == 3:
            self.print_bytex(0xFF)
            self.print_wordx(value)
        elif size == 4:
            self.print_dwordx(value)
        else:
            raise AssertionError()

    def print_bytex(self, byte, pretty_print=None):
        """
        Output an unsigned byte.

        @param byte: Value to output.
        @type  byte: C{int}
        """
        raise NotImplementedError("Implement print_bytex() in {}".format(type(self)))

    def print_wordx(self, byte):
        """
        Output an unsigned word (2 bytes).

        @param byte: Value to output.
        @type  byte: C{int}
        """
        raise NotImplementedError("Implement print_wordx() in {}".format(type(self)))

    def print_dwordx(self, byte):
        """
        Output an unsigned double word (4 bytes).

        @param byte: Value to output.
        @type  byte: C{int}
        """
        raise NotImplementedError("Implement print_dwordx() in {}".format(type(self)))

    def newline(self, msg="", prefix="\t"):
        """
        Output a line separator, prefixed with L{prefix}, C{"// "}, and the
        L{msg}, if the latter is not empty.

        @param msg: Optional message to output first.
        @type  msg: C{str}

        @param prefix: Additional white space in front of the comment.
        @type  prefix: C{str}
        """
        raise NotImplementedError("Implement newline() in {}".format(type(self)))

    def comment(self, msg):
        """
        Output a textual comment at a line by itself.

        @param msg: Comment message.
        @type  msg: C{str}

        @note: Only use if no bytes have been written to the current line.
        """
        raise NotImplementedError("Implement comment() in {}".format(type(self)))

    def start_sprite(self, expected_size, is_real_sprite=False):
        """
        Note to the output stream that a sprite is about to be written.

        @param expected_size: Expected size of the sprite data.
        @type  expected_size: C{int}

        @param is_real_sprite: Self-explanatory.
        @type  is_real_sprite: C{bool}
        """
        del is_real_sprite  # unused in base impl.
        assert not self.in_sprite
        self.in_sprite = True
        self.expected_count = expected_size
        self.byte_count = 0

    def end_sprite(self):
        """
        Note to the output stream that a sprite has been written. The number of
        bytes denoted as expected size with the L{start_sprite} call, should
        have been written.
        """
        assert self.in_sprite
        self.in_sprite = False
        self.newline()
        assert self.expected_count == self.byte_count, "Expected {:d} bytes to be written to sprite, got {:d}".format(
            self.expected_count, self.byte_count
        )


class TextOutputBase(OutputBase):
    """
    Base class for textual output.
    """

    def __init__(self, filename):
        OutputBase.__init__(self, filename)

    def open(self):
        self.file = io.StringIO()


class BinaryOutputBase(SpriteOutputBase):
    """
    Class for binary output.
    """

    def __init__(self, filename):
        SpriteOutputBase.__init__(self, filename)

    def open(self):
        self.file = array.array("B")

    def newline(self, msg="", prefix="\t"):
        pass

    def print_data(self, data):
        """
        Print a chunck of data in one go

        @param data: Data to output
        @type data: C{array}
        """
        self.byte_count += len(data)
        self.file.extend(data)

    def wb(self, byte):
        self.file.append(byte)

    def print_byte(self, value):
        value = self.prepare_byte(value)
        self.wb(value)

    def print_bytex(self, value, pretty_print=None):
        self.print_byte(value)

    def print_word(self, value):
        value = self.prepare_word(value)
        self.wb(value & 0xFF)
        self.wb(value >> 8)

    def print_wordx(self, value):
        self.print_word(value)

    def print_dword(self, value):
        value = self.prepare_dword(value)
        self.wb(value & 0xFF)
        self.wb((value >> 8) & 0xFF)
        self.wb((value >> 16) & 0xFF)
        self.wb(value >> 24)

    def print_dwordx(self, value):
        self.print_dword(value)
