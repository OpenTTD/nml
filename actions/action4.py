import ast
from generic import *
from grfstrings import grf_strings

class Action4:
    def __init__(self, feature, lang, word_sized, id, text):
        self.feature = feature
        self.lang = lang
        self.word_sized = word_sized
        self.id = id
        self.text = text
    
    def write(self, file):
        file.write("-1 * 0 04 ")
        print_bytex(file, self.feature)
        if self.word_sized: self.lang = self.lang | 0x80
        print_bytex(file, self.lang)
        file.write("01 ")
        print_varx(file, self.id, 2 if self.word_sized else 1)
        file.write('"' + self.text + '" ')
        file.write("00\n\n")
    
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
    0xD0: {'random_id': True, 'ids': range(0xFF, -1, -1)},
    0xDC: {'random_id': True, 'ids': range(0x3FF, -1, -1)},
}

def get_string_action4s(feature, string_range, string, id = None):
    global grf_strings, string_ranges
    if not string in grf_strings: raise ScriptError("Unkown string: " + string)
    if string_range != None:
        word_sized = True
        if string_ranges[string_range]['random_id']:
            id = (string_range << 8) | string_ranges[string_range]['ids'].pop()
    else:
        word_sized = False
    
    actions = []
    for translation in grf_strings[string]:
        actions.append(Action4(feature, translation['lang'], not object_specific, id, translation['text']))
    
    return (id, not object_specific, actions)
