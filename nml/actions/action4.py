from nml.generic import *
from nml.grfstrings import grf_strings, get_string_size

class Action4:
    def __init__(self, feature, lang, size, id, text):
        self.feature = feature
        self.lang = lang
        self.size = size
        self.id = id
        self.text = text
    
    def write(self, file):
        # +3 after string size is for final 0 and thorn at the start
        size = 4 + self.size + get_string_size(self.text) + 3
        file.write(str(size) + " 04 ")
        print_bytex(file, self.feature)
        if self.size == 2: self.lang = self.lang | 0x80
        print_bytex(file, self.lang)
        file.write("01 ")
        print_varx(file, self.id, self.size)
        print_string(file, self.text)
        file.write("\n\n")
    
    def skip_action7(self):
        return True
    
    def skip_action9(self):
        return False
    
    def skip_needed(self):
        return True

string_ranges = {
    0xC4: {'random_id': False},
    0xC5: {'random_id': False},
    0xC9: {'random_id': False},
    0xD0: {'random_id': True, 'ids': range(0x3FF, -1, -1)},
    0xDC: {'random_id': True, 'ids': range(0xFF, -1, -1)},
}

def get_string_action4s(feature, string_range, string, id = None):
    global grf_strings, string_ranges
    if not string.name in grf_strings: raise ScriptError("Unkown string: " + string.name)
    if string_range != None:
        size = 2
        if string_ranges[string_range]['random_id']:
            id = string_ranges[string_range]['ids'].pop()
        id = id | (string_range << 8)
    elif feature <= 3:
        size = 3
    else:
        size = 1
    
    actions = []
    for translation in grf_strings[string.name]:
        actions.append(Action4(feature, translation['lang'], size, id, translation['text']))
    
    return (id, size == 2, actions)
