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

class ScriptError(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)

class ConstError(ScriptError):
    def __init__(self):
        ScriptError.__init__(self, "Expected a compile-time constant")

class RangeError(ScriptError):
    def __init__(self, value, min_value, max_value, name):
        ScriptError.__init__(self, name + " out of range " + str(min_value) + ".." + str(max_value) + ", encountered " + str(value))
