from nml import generic, grfstrings
from nml.actions import base_action

class Action4(base_action.BaseAction):
    def __init__(self, feature, lang, size, id, text):
        self.feature = feature
        self.lang = lang
        self.size = size
        self.id = id
        self.text = text

    def prepare_output(self):
        if self.size == 2: self.lang = self.lang | 0x80

    def write(self, file):
        size = 4 + self.size + grfstrings.get_string_size(self.text)
        file.start_sprite(size)
        file.print_bytex(4)
        file.print_bytex(self.feature)
        file.print_bytex(self.lang)
        file.print_bytex(1)
        file.print_varx(self.id, self.size)
        file.print_string(self.text)
        file.newline()
        file.end_sprite()

    def skip_action9(self):
        return False

string_ranges = {
    0xC4: {'random_id': False},
    0xC5: {'random_id': False},
    0xC9: {'random_id': False},
    0xD0: {'random_id': True, 'ids': range(0x3FF, -1, -1)},
    0xDC: {'random_id': True, 'ids': range(0xFF, -1, -1)},
}

used_strings = {
    0xD0: {},
    0xDC: {},
}

def get_global_string_actions():
    actions = []
    for string_range, strings in used_strings.iteritems():
        for string_name, id in strings.iteritems():
            for translation in grfstrings.grf_strings[string_name]:
                actions.append(Action4(0x08, translation['lang'], 2, (string_range << 8) | id, translation['text']))
    return actions

def get_string_action4s(feature, string_range, string, id = None):
    global string_ranges
    if not string.name.value in grfstrings.grf_strings: raise generic.ScriptError("Unknown string: " + string.name.value, string.pos)
    write_action4s = True
    if string_range is not None:
        size = 2
        if string_ranges[string_range]['random_id']:
            write_action4s = False
            if string.name.value in used_strings[string_range]:
                id = used_strings[string_range][string.name.value]
            else:
                id = string_ranges[string_range]['ids'].pop()
                used_strings[string_range][string.name.value] = id
        id = id | (string_range << 8)
    elif feature <= 3:
        size = 3
    else:
        size = 1

    actions = []
    if write_action4s:
        for translation in grfstrings.grf_strings[string.name.value]:
            actions.append(Action4(feature, translation['lang'], size, id, translation['text']))

    actions.sort(key=lambda action: action.lang);

    return (id, size == 2, actions)
