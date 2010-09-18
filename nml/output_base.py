"""
Abstract base classes that implements common functionality for output classes
"""
class OutputBase(object):
    """
    Base class for output to a data file.
    """
    def __init__(self):
        pass

class BinaryOutputBase(OutputBase):
    """
    Base class for output to a binary data file.
    """
    def __init__(self):
        OutputBase.__init__(self)
        self._in_sprite = False

    def prepare_byte(self, value):
        assert self._in_sprite
        if -0x80 < value < 0 : value += 0x100
        assert value >= 0 and value <= 0xFF
        self._byte_count += 1
        return value

    def prepare_word(self, value):
        assert self._in_sprite
        if -0x8000 < value < 0: value += 0x10000
        assert value >= 0 and value <= 0xFFFF
        self._byte_count += 2
        return value

    def prepare_dword(self, value):
        assert self._in_sprite
        if -0x80000000 < value < 0: value += 0x100000000
        assert value >= 0 and value <= 0xFFFFFFFF
        self._byte_count += 4
        return value

    def print_varx(self, value, size):
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
            assert False

    def print_bytex(self, byte, pretty_print = None):
        """
        Output an unsigned byte.

        @param byte: Value to output.
        @type  byte: C{int}
        """
        raise NotImplementedError("Implement print_bytex() in %r" % type(self))

    def print_wordx(self, byte):
        """
        Output an unsigned word (2 bytes).

        @param byte: Value to output.
        @type  byte: C{int}
        """
        raise NotImplementedError("Implement print_wordx() in %r" % type(self))

    def print_dwordx(self, byte):
        """
        Output an unsigned double word (4 bytes).

        @param byte: Value to output.
        @type  byte: C{int}
        """
        raise NotImplementedError("Implement print_dwordx() in %r" % type(self))

    def newline(self):
        """
        Output a seperator.
        """
        raise NotImplementedError("Implement newline() in %r" % type(self))


    def start_sprite(self, size):
        assert not self._in_sprite
        self._in_sprite = True
        self._expected_count = size
        self._byte_count = 0

    def end_sprite(self):
        assert self._in_sprite
        self._in_sprite = False
        self.newline()
        assert self._expected_count == self._byte_count, "Expected %d bytes to be written to sprite, got %d" % (self._expected_count, self._byte_count)
