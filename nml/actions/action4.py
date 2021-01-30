__license__ = """
NML is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

NML is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License along
with NML; if not, write to the Free Software Foundation, Inc.,
51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA."""

from nml import expression, generic, grfstrings
from nml.actions import action6, actionD, base_action


class Action4(base_action.BaseAction):
    """
    Class representing a single action 4.
    Format: 04 <feature> <language-id> <num-ent> <offset> <text>

    @ivar feature: Feature of this action 4
    @type feature: C{int}

    @ivar lang: Language ID of the text (set as ##grflangid in the .lng file, 0x7F for default)
    @type lang: C{int}

    @ivar size: Size of the id, may be 1 (byte), 2 (word) or 3 (ext. byte)
    @type size: C{int}

    @ivar id: ID of the first string to write
    @type id: C{int}

    @ivar texts: List of strings to write
    @type texts: C{list} of C{str}
    """

    def __init__(self, feature, lang, size, id, texts):
        self.feature = feature
        self.lang = lang
        self.size = size
        self.id = id
        self.texts = texts

    def prepare_output(self, sprite_num):
        # To indicate a word value, bit 7 of the lang ID must be set
        if self.size == 2:
            self.lang = self.lang | 0x80

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


# List of various string ranges that may be used
# Attributes:
#  - random_id: If true, string IDs may be allocated randomly, else the ID has a special meaning and must be assigned
#               (e.g. for vehicles, string ID = vehicle ID)
#  - ids: List of free IDs, only needed if random_id is true. Whenever an ID is used, it's removed from the list
string_ranges = {
    0xC4: {"random_id": False},  # Station class names
    0xC5: {"random_id": False},  # Station names
    0xC9: {"random_id": False},  # House name
    # Misc. text ids, used for callbacks and such
    0xD0: {"random_id": True, "total": 0x400, "ids": list(range(0xD3FF, 0xCFFF, -1))},
    # Misc. persistent text ids, used to set properties.
    # Use Ids DC00..DCFF first to keep compatibility with older versions of OTTD.
    0xDC: {"random_id": True, "total": 0x800, "ids": list(range(0xDBFF, 0xD7FF, -1)) + list(range(0xDFFF, 0xDBFF, -1))},
}

# Mapping of string identifiers to D0xx/DCxx text ids
# This allows outputting strings only once, instead of everywhere they are used
used_strings = {
    0xD0: {},
    0xDC: {},
}


def print_stats():
    """
    Print statistics about used ids.
    """
    for t, l in string_ranges.items():
        if l["random_id"]:
            num_used = l["total"] - len(l["ids"])
            if num_used > 0:
                generic.print_info("{:02X}xx strings: {}/{}".format(t, num_used, l["total"]))


def get_global_string_actions():
    """
    Get a list of global string actions
    i.e. print all D0xx / DCxx texts at once

    @return: A list of all D0xx / DCxx action4s
    @rtype: C{list} of L{BaseAction}
    """
    texts = []
    actions = []
    for strings in used_strings.values():
        for feature_name, id in strings.items():
            feature, string_name = feature_name
            texts.append((0x7F, id, grfstrings.get_translation(string_name), feature))
            for lang_id in grfstrings.get_translations(string_name):
                texts.append((lang_id, id, grfstrings.get_translation(string_name, lang_id), feature))

    last_lang = -1
    last_id = -1
    last_feature = -1
    # Sort to have a deterministic ordering and to have as much consecutive IDs as possible
    texts.sort(key=lambda text: (-1 if text[0] == 0x7F else text[0], text[1]))

    for text in texts:
        str_lang, str_id, str_text, feature = text
        # If possible, append strings to the last action 4 instead of creating a new one
        if str_lang != last_lang or str_id - 1 != last_id or feature != last_feature or len(actions[-1].texts) == 0xFF:
            actions.append(Action4(feature, str_lang, 2, str_id, [str_text]))
        else:
            actions[-1].texts.append(str_text)
        last_lang = str_lang
        last_id = str_id
        last_feature = feature
    return actions


def get_string_action4s(feature, string_range, string, id=None):
    """
    Let a string from the lang files be used in the rest of NML.
    This may involve adding actions directly, but otherwise an ID is allocated and the string will be written later

    @param feature: Feature that uses the string
    @type feature: C{int}

    @param string_range: String range to use, either a value from L{string_ranges} or C{None} if N/A (item names)
    @type string_range: C{int} or C{None}

    @param string: String to parse
    @type string: L{expression.String}

    @param id: ID to use for this string, or C{None} if it will be allocated dynamically
               (random_id is true for the string range)
    @type id: L{Expression} or C{None}

    @return: A tuple of two values:
                - ID of the string (useful if allocated dynamically)
                - Resulting action list to be appended
    @rtype: C{tuple} of (C{int}, C{list} of L{BaseAction})
    """
    grfstrings.validate_string(string)
    write_action4s = True
    action6.free_parameters.save()
    actions = []

    mod = None
    if string_range is not None:
        size = 2
        if string_ranges[string_range]["random_id"]:
            # ID is allocated randomly, we will output the actions later
            write_action4s = False
            if (feature, string) in used_strings[string_range]:
                id_val = used_strings[string_range][(feature, string)]
            else:
                try:
                    id_val = string_ranges[string_range]["ids"].pop()
                    used_strings[string_range][(feature, string)] = id_val
                except IndexError:
                    raise generic.ScriptError(
                        "Unable to allocate ID for string, no more free IDs available (maximum is {:d})".format(
                            string_ranges[string_range]["total"]
                        ),
                        string.pos,
                    )
        else:
            # ID must be supplied
            assert id is not None
            assert isinstance(id, expression.ConstantNumeric)
            id_val = id.value | (string_range << 8)
    else:
        # Not a string range, so we must have an id
        assert id is not None
        size = 3 if feature <= 3 else 1
        if isinstance(id, expression.ConstantNumeric):
            id_val = id.value
        else:
            id_val = 0
            tmp_param, tmp_param_actions = actionD.get_tmp_parameter(id)
            actions.extend(tmp_param_actions)
            # Apply ID via action4 later
            mod = (tmp_param, 2 if feature <= 3 else 1, 5 if feature <= 3 else 4)

    if write_action4s:
        strings = [
            (lang_id, grfstrings.get_translation(string, lang_id)) for lang_id in grfstrings.get_translations(string)
        ]
        # Sort the strings for deterministic ordering and prepend the default language
        strings = [(0x7F, grfstrings.get_translation(string))] + sorted(strings, key=lambda lang_text: lang_text[0])

        for lang_id, text in strings:
            if mod is not None:
                act6 = action6.Action6()
                act6.modify_bytes(*mod)
                actions.append(act6)
            actions.append(Action4(feature, lang_id, size, id_val, [text]))

    action6.free_parameters.restore()

    return (id_val, actions)
