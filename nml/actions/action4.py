from nml import grfstrings
from nml.actions import base_action

class Action4(base_action.BaseAction):
    def __init__(self, feature, lang, size, id, texts):
        self.feature = feature
        self.lang = lang
        self.size = size
        self.id = id
        self.texts = texts

    def prepare_output(self):
        if self.size == 2: self.lang = self.lang | 0x80

    def write(self, file):
        size = 4 + self.size
        for text in self.texts:
            size += grfstrings.get_string_size(text)
        file.start_sprite(size)
        file.print_bytex(4)
        file.print_bytex(self.feature)
        file.print_bytex(self.lang)
        file.print_bytex(len(self.texts))
        file.print_varx(self.id, self.size)
        for text in self.texts:
            file.print_string(text)
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
    texts = []
    actions = []
    for string_range, strings in used_strings.iteritems():
        for string_name, id in strings.iteritems():
            texts.append( (0x7F, (string_range << 8) | id, grfstrings.get_translation(string_name)) )
            for lang_id in grfstrings.get_translations(string_name):
                texts.append( (lang_id, (string_range << 8) | id, grfstrings.get_translation(string_name, lang_id)) )
    last_lang = -1
    last_id = -1
    texts.sort(key=lambda text: (-1 if text[0] == 0x7F else text[0], text[1]))
    for text in texts:
        str_lang, str_id, str_text = text
        if str_lang != last_lang or str_id - 1 != last_id:
            actions.append(Action4(0x08, str_lang, 2, str_id, [str_text]))
        else:
            actions[-1].texts.append(str_text)
        last_lang = str_lang
        last_id = str_id
    return actions

def get_string_action4s(feature, string_range, string, id = None):
    global string_ranges
    grfstrings.validate_string(string)
    write_action4s = True
    if string_range is not None:
        size = 2
        if string_ranges[string_range]['random_id']:
            write_action4s = False
            if string in used_strings[string_range]:
                id = used_strings[string_range][string]
            else:
                id = string_ranges[string_range]['ids'].pop()
                used_strings[string_range][string] = id
        id = id | (string_range << 8)
    elif feature <= 3:
        size = 3
    else:
        size = 1

    actions = []
    if write_action4s:
        actions.append(Action4(feature, 0x7F, size, id, [grfstrings.get_translation(string)]))
        for lang_id in grfstrings.get_translations(string):
            actions.append(Action4(feature, lang_id, size, id, [grfstrings.get_translation(string, lang_id)]))

    actions.sort(key=lambda action: action.lang);

    return (id, size == 2, actions)
