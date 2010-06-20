from nml import generic, grfstrings

class Action4(object):
    def __init__(self, feature, lang, size, id, text):
        self.feature = feature
        self.lang = lang
        self.size = size
        self.id = id
        self.text = text

    def prepare_output(self):
        if self.size == 2: self.lang = self.lang | 0x80

    def write(self, file):
        # +3 after string size is for final 0 and thorn at the start
        size = 4 + self.size + grfstrings.get_string_size(self.text) + 3
        file.start_sprite(size)
        file.print_bytex(4)
        file.print_bytex(self.feature)
        file.print_bytex(self.lang)
        file.print_bytex(1)
        file.print_varx(self.id, self.size)
        file.print_string(self.text)
        file.newline()
        file.end_sprite()

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
    global string_ranges
    if not string.name.value in grfstrings.grf_strings: raise generic.ScriptError("Unknown string: " + string.name.value, string.pos)
    if string_range is not None:
        size = 2
        if string_ranges[string_range]['random_id']:
            id = string_ranges[string_range]['ids'].pop()
        id = id | (string_range << 8)
    elif feature <= 3:
        size = 3
    else:
        size = 1

    actions = []
    for translation in grfstrings.grf_strings[string.name.value]:
        actions.append(Action4(feature, translation['lang'], size, id, translation['text']))

    return (id, size == 2, actions)
