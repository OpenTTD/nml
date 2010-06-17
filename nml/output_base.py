"""
Abstract base class that implements common functionality for output classes
"""
class OutputBase(object):
    def __init__(self):
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

    def start_sprite(self, size):
        assert not self._in_sprite
        self._in_sprite = True
        self._expected_count = size
        self._byte_count = 0

    def end_sprite(self):
        assert self._in_sprite
        self._in_sprite = False
        self.newline()
        if self._expected_count != self._byte_count:
            raise "Expected %d bytes to be written, got %d" % (self._expected_count, self._byte_count)
