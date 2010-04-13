# -*- coding: utf-8 -*-

def to_hex(value, width = 0):
    ret = hex(value)[2:].upper()
    if ret[-1] == 'L': ret = ret[0:-1]
    return ret.zfill(width)

def print_byte(file, value):
    if -0x80 < value < 0 : value += 0x100
    assert value >= 0 and value <= 0xFF
    file.write("\\b" + str(value) + " ")

def print_extended_byte(file, value):
    if -0x8000 < value < 0: value += 0x10000
    assert value >= 0 and value <= 0xFFFF
    file.write("\\b*" + str(value) + " ")

def print_bytex(file, value):
    if -0x80 < value < 0: value += 0x100
    assert value >= 0 and value <= 0xFF
    file.write(to_hex(value, 2) + " ")

def print_word(file, value):
    if -0x8000 < value < 0: value += 0x10000
    assert value >= 0 and value <= 0xFFFF
    file.write("\\w" + str(value) + " ")

def print_wordx(file, value):
    if -0x8000 < value < 0: value += 0x10000
    assert value >= 0 and value <= 0xFFFF
    file.write("\\wx" + to_hex(value, 4) + " ")

def print_dword(file, value):
    if -0x80000000 < value < 0: value += 0x100000000
    assert value >= 0 and value <= 0xFFFFFFFF
    file.write("\\d" + str(value) + " ")

def print_dwordx(file, value):
    if -0x80000000 < value < 0: value += 0x100000000
    assert value >= 0 and value <= 0xFFFFFFFF
    file.write("\\dx" + to_hex(value, 8) + " ")

def print_varx(file, value, size):
    if size == 1:
        print_bytex(file, value)
    elif size == 2:
        print_wordx(file, value)
    elif size == 4:
        print_dwordx(file, value)
    else:
        assert False

def print_string(file, value, final_zero = True, force_ascii = False):
    file.write('"')
    if not force_ascii: file.write(u'Þ')
    file.write(value)
    file.write('" ')
    if final_zero: file.write('00 ')

def print_decimal(file, value):
    file.write(str(value) + " ")

def truncate_int32(value):
    #source: http://www.tiac.net/~sw/2010/02/PureSalsa20/index.html
    return int( (value & 0x7fffFFFF) | -(value & 0x80000000) )

class ScriptError(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)
