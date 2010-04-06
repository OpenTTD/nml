def to_hex(value):
    ret = hex(value)[2:].upper()
    if ret[-1] == 'L': ret = ret[0:-1]
    return ret

def print_byte(file, value):
    assert value >= 0 and value < 256
    file.write("\\b" + str(value) + " ")

def print_extended_byte(file, value):
    assert value >= 0 and value < 65536
    file.write("\\b*" + str(value) + " ")

def print_bytex(file, value):
    assert value >= 0 and value < 256
    file.write(to_hex(value).zfill(2) + " ")

def print_word(file, value):
    assert value >= 0 and value < 65536
    file.write("\\w" + str(value) + " ")

def print_wordx(file, value):
    assert value >= 0 and value < 65536
    file.write("\\wx" + to_hex(value).zfill(4) + " ")

def print_dword(file, value):
    assert value >= 0 and value < 4294967296
    file.write("\\d" + str(value) + " ")

def print_dwordx(file, value):
    assert value >= 0 and value < 4294967296
    file.write("\\dx" + to_hex(value).zfill(8) + " ")

def print_varx(file, value, size):
    if size == 1:
        print_bytex(file, value)
    elif size == 2:
        print_wordx(file, value)
    elif size == 4:
        print_dwordx(file, value)
    else:
        assert False

def print_string(file, value):
    file.write('"' + value + '" 00 ')

class ScriptError(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)
