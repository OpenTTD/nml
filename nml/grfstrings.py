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

import glob
import os
import re

from nml import generic


def utf8_get_size(char):
    if char < 128:
        return 1
    if char < 2048:
        return 2
    if char < 65536:
        return 3
    return 4


DEFAULT_LANGUAGE = 0x7F
DEFAULT_LANGNAME = "english.lng"


def validate_string(string):
    """
    Check if a given string refers to a string that is translated in the language
    files and raise an error otherwise.

    @param string: The string to validate.
    @type  string: L{expression.String}
    """
    if string.name.value not in default_lang.strings:
        raise generic.ScriptError('Unknown string "{}"'.format(string.name.value), string.pos)


def is_ascii_string(string):
    """
    Check whether a given string can be written using the ASCII codeset or
    that we need unicode.

    @param string: The string to check.
    @type  string: C{str}

    @return: True iff the string is ascii-only.
    @rtype:  C{bool}
    """
    assert isinstance(string, str)
    i = 0
    while i < len(string):
        if string[i] != "\\":
            if ord(string[i]) >= 0x7B:
                return False
            i += 1
        else:
            if string[i + 1] in ("\\", '"'):
                i += 2
            elif string[i + 1] == "U":
                return False
            else:
                i += 3
    return True


def get_string_size(string, final_zero=True, force_ascii=False):
    """
    Get the size (in bytes) of a given string.

    @param string: The string to check.
    @type  string: C{str}

    @param final_zero: Whether or not to account for a zero-byte directly after the string.
    @type  final_zero: C{bool}

    @param force_ascii: When true, make sure the string is written as ascii as opposed to unicode.
    @type  force_ascii: C{bool}

    @return: The length (in bytes) of the given string.
    @rtype:  C{int}

    @raise generic.ScriptError: force_ascii and not is_ascii_string(string).
    """
    size = 0
    if final_zero:
        size += 1
    if not is_ascii_string(string):
        if force_ascii:
            raise generic.ScriptError("Expected ascii string but got a unicode string")
        size += 2
    i = 0
    while i < len(string):
        if string[i] != "\\":
            size += utf8_get_size(ord(string[i]))
            i += 1
        else:
            if string[i + 1] in ("\\", '"'):
                size += 1
                i += 2
            elif string[i + 1] == "U":
                size += utf8_get_size(int(string[i + 2 : i + 6], 16))
                i += 6
            else:
                size += 1
                i += 3
    return size


def get_translation(string, lang_id=DEFAULT_LANGUAGE):
    """
    Get the translation of a given string in a certain language. If there is no
    translation available in the given language return the default translation.

    @param string: the string to get the translation for.
    @type  string: L{expression.String}

    @param lang_id: The language id of the language to translate the string into.
    @type  lang_id: C{int}

    @return: Translation of the given string in the given language.
    @rtype:  C{str}
    """
    for lang_pair in langs:
        langid, lang = lang_pair
        if langid != lang_id:
            continue
        if string.name.value not in lang.strings:
            break
        return lang.get_string(string, lang_id)
    return default_lang.get_string(string, lang_id)


def get_translations(string):
    """
    Get a list of language ids that have a translation for the given string.

    @param string: the string to get the translations for.
    @type  string: L{expression.String}

    @return: List of languages that translate the given string.
    @rtype:  C{list} of C{int}
    """
    translations = []
    for lang_pair in langs:
        langid, lang = lang_pair
        assert langid is not None
        if string.name.value in lang.strings and lang.get_string(string, langid) != default_lang.get_string(
            string, langid
        ):
            translations.append(langid)

    # Also check for translated substrings
    import nml.expression

    for param in string.params:
        if not isinstance(param, nml.expression.String):
            continue
        param_translations = get_translations(param)
        translations.extend([langid for langid in param_translations if langid not in translations])

    return translations


def com_parse_comma(val, lang_id):
    val = val.reduce_constant()
    return str(val)


def com_parse_hex(val, lang_id):
    val = val.reduce_constant()
    return "0x{:X}".format(val.value)


def com_parse_string(val, lang_id):
    import nml.expression

    if not isinstance(val, (nml.expression.StringLiteral, nml.expression.String)):
        raise generic.ScriptError("Expected a (literal) string", val.pos)
    if isinstance(val, nml.expression.String):
        # Check that the string exists
        if val.name.value not in default_lang.strings:
            raise generic.ScriptError('Substring "{}" does not exist'.format(val.name.value), val.pos)
        return get_translation(val, lang_id)
    return val.value


# fmt: off
commands = {
    # Special characters / glyphs
    "":               {"unicode": r"\0D",       "ascii": r"\0D"},
    "{":              {"unicode": r"{",         "ascii": r"{"},
    "NBSP":           {"unicode": r"\U00A0"},  # character A0 is used as up arrow in TTD, so don"t use ASCII here.
    "COPYRIGHT":      {"unicode": r"\U00A9",    "ascii": r"\A9"},
    "TRAIN":          {"unicode": r"\UE0B4",    "ascii": r"\B4"},
    "LORRY":          {"unicode": r"\UE0B5",    "ascii": r"\B5"},
    "BUS":            {"unicode": r"\UE0B6",    "ascii": r"\B6"},
    "PLANE":          {"unicode": r"\UE0B7",    "ascii": r"\B7"},
    "SHIP":           {"unicode": r"\UE0B8",    "ascii": r"\B8"},

    # Change the font size.
    "TINYFONT":       {"unicode": r"\0E",       "ascii": r"\0E"},
    "BIGFONT":        {"unicode": r"\0F",       "ascii": r"\0F"},

    "COMMA":          {"unicode": r"\UE07B",    "ascii": r"\7B", "size": 4, "parse": com_parse_comma},
    "SIGNED_WORD":    {"unicode": r"\UE07C",    "ascii": r"\7C", "size": 2, "parse": com_parse_comma},
    "UNSIGNED_WORD":  {"unicode": r"\UE07E",    "ascii": r"\7E", "size": 2, "parse": com_parse_comma},
    "CURRENCY":       {"unicode": r"\UE07F",    "ascii": r"\7F", "size": 4},
    "STRING": {
        "unicode":    r"\UE080",
        "ascii":      r"\80",
        "allow_case": True,
        "size":       2,
        "parse":      com_parse_string
    },
    "DATE1920_LONG":  {"unicode": r"\UE082",    "ascii": r"\82", "size": 2},
    "DATE1920_SHORT": {"unicode": r"\UE083",    "ascii": r"\83", "size": 2},
    "VELOCITY":       {"unicode": r"\UE084",    "ascii": r"\84", "size": 2},
    "SKIP":           {"unicode": r"\UE085",    "ascii": r"\85", "size": 2},
    "VOLUME":         {"unicode": r"\UE087",    "ascii": r"\87", "size": 2},
    "HEX":            {"unicode": r"\UE09A\08", "ascii": r"\9A\08", "size": 4, "parse": com_parse_hex},
    "STATION":        {"unicode": r"\UE09A\0C", "ascii": r"\9A\0C", "size": 2},
    "WEIGHT":         {"unicode": r"\UE09A\0D", "ascii": r"\9A\0D", "size": 2},
    "DATE_LONG":      {"unicode": r"\UE09A\16", "ascii": r"\9A\16", "size": 4},
    "DATE_SHORT":     {"unicode": r"\UE09A\17", "ascii": r"\9A\17", "size": 4},
    "POWER":          {"unicode": r"\UE09A\18", "ascii": r"\9A\18", "size": 2},
    "VOLUME_SHORT":   {"unicode": r"\UE09A\19", "ascii": r"\9A\19", "size": 2},
    "WEIGHT_SHORT":   {"unicode": r"\UE09A\1A", "ascii": r"\9A\1A", "size": 2},
    "CARGO_LONG":     {"unicode": r"\UE09A\1B", "ascii": r"\9A\1B", "size": 2 * 2},
    "CARGO_SHORT":    {"unicode": r"\UE09A\1C", "ascii": r"\9A\1C", "size": 2 * 2},
    "CARGO_TINY":     {"unicode": r"\UE09A\1D", "ascii": r"\9A\1D", "size": 2 * 2},
    "CARGO_NAME":     {"unicode": r"\UE09A\1E", "ascii": r"\9A\1E", "size": 2},
    "FORCE":          {"unicode": r"\UE09A\21", "ascii": r"\9A\21", "size": 4},

    # Colors
    "BLUE":           {"unicode": r"\UE088",    "ascii": r"\88"},
    "SILVER":         {"unicode": r"\UE089",    "ascii": r"\89"},
    "GOLD":           {"unicode": r"\UE08A",    "ascii": r"\8A"},
    "RED":            {"unicode": r"\UE08B",    "ascii": r"\8B"},
    "PURPLE":         {"unicode": r"\UE08C",    "ascii": r"\8C"},
    "LTBROWN":        {"unicode": r"\UE08D",    "ascii": r"\8D"},
    "ORANGE":         {"unicode": r"\UE08E",    "ascii": r"\8E"},
    "GREEN":          {"unicode": r"\UE08F",    "ascii": r"\8F"},
    "YELLOW":         {"unicode": r"\UE090",    "ascii": r"\90"},
    "DKGREEN":        {"unicode": r"\UE091",    "ascii": r"\91"},
    "CREAM":          {"unicode": r"\UE092",    "ascii": r"\92"},
    "BROWN":          {"unicode": r"\UE093",    "ascii": r"\93"},
    "WHITE":          {"unicode": r"\UE094",    "ascii": r"\94"},
    "LTBLUE":         {"unicode": r"\UE095",    "ascii": r"\95"},
    "GRAY":           {"unicode": r"\UE096",    "ascii": r"\96"},
    "DKBLUE":         {"unicode": r"\UE097",    "ascii": r"\97"},
    "BLACK":          {"unicode": r"\UE098",    "ascii": r"\98"},

    "PUSH_COLOUR":    {"unicode": r"\UE09A\1F", "ascii": r"\9A\1F"},
    "POP_COLOUR":     {"unicode": r"\UE09A\20", "ascii": r"\9A\20"},

    # Deprecated string codes
    "DWORD_S":        {"unicode": r"\UE07B",    "ascii": r"\7B", "deprecated": True, "size": 4},
    "PARAM":          {"unicode": r"\UE07B",    "ascii": r"\7B", "deprecated": True, "size": 4},
    "WORD_S":         {"unicode": r"\UE07C",    "ascii": r"\7C", "deprecated": True, "size": 2},
    "BYTE_S":         {"unicode": r"\UE07D",    "ascii": r"\7D", "deprecated": True},
    "WORD_U":         {"unicode": r"\UE07E",    "ascii": r"\7E", "deprecated": True, "size": 2},
    "POP_WORD":       {"unicode": r"\UE085",    "ascii": r"\85", "deprecated": True, "size": 2},
    "CURRENCY_QWORD": {"unicode": r"\UE09A\01", "ascii": r"\9A\01", "deprecated": True},
    "PUSH_WORD":      {"unicode": r"\UE09A\03", "ascii": r"\9A\03", "deprecated": True},
    "UNPRINT":        {"unicode": r"\UE09A\04", "ascii": r"\9A\04", "deprecated": True},
    "BYTE_HEX":       {"unicode": r"\UE09A\06", "ascii": r"\9A\06", "deprecated": True},
    "WORD_HEX":       {"unicode": r"\UE09A\07", "ascii": r"\9A\07", "deprecated": True, "size": 2},
    "DWORD_HEX":      {"unicode": r"\UE09A\08", "ascii": r"\9A\08", "deprecated": True, "size": 4},
    "QWORD_HEX":      {"unicode": r"\UE09A\0B", "ascii": r"\9A\0B", "deprecated": True},
    "WORD_S_TONNES":  {"unicode": r"\UE09A\0D", "ascii": r"\9A\0D", "deprecated": True, "size": 2},
}
# fmt: on

special_commands = [
    "P",
    "G",
    "G=",
]


def read_extra_commands(custom_tags_file):
    """
    @param custom_tags_file: Filename of the custom tags file.
    @type  custom_tags_file: C{str}
    """
    if not os.access(custom_tags_file, os.R_OK):
        # Failed to open custom_tags.txt, ignore this
        return
    line_no = 0
    with open(generic.find_file(custom_tags_file), "r", encoding="utf-8") as fh:
        for line in fh:
            line_no += 1
            line = line.strip()
            if len(line) == 0 or line[0] == "#":
                continue

            i = line.find(":")
            if i == -1:
                raise generic.ScriptError("Line has no ':' delimiter.", generic.LinePosition(custom_tags_file, line_no))
            name = line[:i].strip()
            value = line[i + 1 :]
            if name in commands:
                generic.print_warning(
                    generic.Warning.GENERIC,
                    'Overwriting existing tag "' + name + '".',
                    generic.LinePosition(custom_tags_file, line_no),
                )
            commands[name] = {"unicode": value}
            if is_ascii_string(value):
                commands[name]["ascii"] = value


class StringCommand:
    """
    Instantiated string command.

    @ivar name: Name of the string command.
    @type name: C{str}

    @ivar case: ???
    @type case: ???

    @ivar arguments: Arguments of the instantiated command.
    @type arguments: C{list} of ???

    @ivar offset: Index to an argument of the P or G string command (ie "2" in {P 2 ...}), if available.
    @type offset: C{int} or C{None}

    @ivar str_pos: String argument index ("2" in {2:FOO..}, if available.
    @type str_pos: C{int} or C{None}

    @ivar pos: Position of the string.
    @type pos: L{Position}
    """

    def __init__(self, name, str_pos, pos):
        assert name in commands or name in special_commands
        self.name = name
        self.case = None
        self.arguments = []
        self.offset = None
        self.str_pos = str_pos
        self.pos = pos

    def set_arguments(self, arg_string):
        start = -1
        cur = 0
        quoted = False
        whitespace = " \t"
        while cur < len(arg_string):
            if start != -1:
                if (quoted and arg_string[cur] == '"') or (not quoted and arg_string[cur] in whitespace):
                    if (
                        not quoted
                        and self.offset is None
                        and len(self.arguments) == 0
                        and isint(arg_string[start:cur])
                        and self.name in ("P", "G")
                    ):
                        self.offset = int(arg_string[start:cur])
                    else:
                        self.arguments.append(arg_string[start:cur])
                    start = -1
            elif arg_string[cur] not in whitespace:
                quoted = arg_string[cur] == '"'
                start = cur + 1 if quoted else cur
            cur += 1
        if start != -1 and not quoted:
            self.arguments.append(arg_string[start:])
            start = -1
        return start == -1

    def validate_arguments(self, lang):
        if lang.langid == DEFAULT_LANGUAGE:
            return
        if self.name == "P":
            if not lang.has_plural_pragma():
                raise generic.ScriptError("Using {P} without a ##plural pragma", self.pos)
            if len(self.arguments) != lang.get_num_plurals():
                raise generic.ScriptError(
                    "Invalid number of arguments to plural command, expected {:d} but got {:d}".format(
                        lang.get_num_plurals(), len(self.arguments)
                    ),
                    self.pos,
                )
        elif self.name == "G":
            if not lang.has_gender_pragma():
                raise generic.ScriptError("Using {G} without a ##gender pragma", self.pos)
            if len(self.arguments) != len(lang.genders):
                raise generic.ScriptError(
                    "Invalid number of arguments to gender command, expected {:d} but got {:d}".format(
                        len(lang.genders), len(self.arguments)
                    ),
                    self.pos,
                )
        elif self.name == "G=":
            if not lang.has_gender_pragma():
                raise generic.ScriptError("Using {G=} without a ##gender pragma", self.pos)
            if len(self.arguments) != 1:
                raise generic.ScriptError(
                    "Invalid number of arguments to set-gender command, expected {:d} but got {:d}".format(
                        1, len(self.arguments)
                    ),
                    self.pos,
                )
        elif len(self.arguments) != 0:
            raise generic.ScriptError('Unexpected arguments to command "{}"'.format(self.name), self.pos)

    def parse_string(self, str_type, lang, wanted_lang_id, prev_command, stack, static_args):
        """
        Convert the string command to output text.

        @param str_type: Exptected type of result text, C{"unicode"} or C{"ascii"}.
        @type  str_type: C{str}

        @param lang: Language of the string.
        @type  lang: L{Language}

        @param wanted_lang_id: Language-id to use for interpreting the command
                               (this string may be from another language, eg with missing strings).

        @param prev_command: Argument of previous string command (parameter number, size).
        @type  prev_command: C{tuple} or C{None}

        @param stack: Stack of available arguments (list of (parameter number, size)).
        @type  stack: C{list} of C{tuple} (C{int}, C{int}) or C{None}

        @param static_args: Static command arguments.
        """
        if self.name in commands:
            if not self.is_important_command():
                return commands[self.name][str_type]
            # Compute position of the argument in the stack.
            stack_pos = 0
            for pos, size in stack:
                if pos == self.str_pos:
                    break
                stack_pos += size
            self_size = commands[self.name]["size"]
            stack.remove((self.str_pos, self_size))
            if self.str_pos < len(static_args):
                if "parse" not in commands[self.name]:
                    raise generic.ScriptError(
                        "Provided a static argument for string command '{}' which is invalid".format(self.name),
                        self.pos,
                    )
                # Parse commands using the wanted (not current) lang id, so translations are used if present
                return commands[self.name]["parse"](static_args[self.str_pos], wanted_lang_id)
            prefix = ""
            suffix = ""
            if self.case:
                prefix += STRING_SELECT_CASE[str_type] + "\\{:02X}".format(self.case)
            if stack_pos + self_size > 8:
                raise generic.ScriptError(
                    "Trying to read an argument from the stack without reading the arguments before", self.pos
                )
            if self_size == 4 and stack_pos == 4:
                prefix += STRING_ROTATE[str_type] + STRING_ROTATE[str_type]
            elif self_size == 4 and stack_pos == 2:
                prefix += STRING_PUSH_WORD[str_type] + STRING_ROTATE[str_type] + STRING_ROTATE[str_type]
                suffix += STRING_SKIP[str_type]
            elif self_size == 2 and stack_pos == 6:
                prefix += STRING_ROTATE[str_type]
            elif self_size == 2 and stack_pos == 4:
                prefix += STRING_PUSH_WORD[str_type] + STRING_ROTATE[str_type]
                suffix += STRING_SKIP[str_type]
            elif self_size == 2 and stack_pos == 2:
                prefix += STRING_PUSH_WORD[str_type] + STRING_PUSH_WORD[str_type] + STRING_ROTATE[str_type]
                suffix += STRING_SKIP[str_type] + STRING_SKIP[str_type]
            else:
                assert stack_pos == 0
            return prefix + commands[self.name][str_type] + suffix
        assert self.name in special_commands
        # Create a local copy because we shouldn't modify the original
        offset = self.offset
        if offset is None:
            if self.name == "P":
                if not prev_command:
                    raise generic.ScriptError(
                        "A plural choice list {P} has to be preceded by another string code or provide an offset",
                        self.pos,
                    )
                offset = prev_command[0]
            else:
                if not stack:
                    raise generic.ScriptError(
                        "A gender choice list {G} has to be followed by another string code or provide an offset",
                        self.pos,
                    )
                offset = stack[0][0]
        offset -= len(static_args)
        if self.name == "P":
            if offset < 0:
                return self.arguments[lang.static_plural_form(static_args[offset]) - 1]
            ret = BEGIN_PLURAL_CHOICE_LIST[str_type] + "\\{:02X}".format(0x80 + offset)
            for idx, arg in enumerate(self.arguments):
                if idx == len(self.arguments) - 1:
                    ret += CHOICE_LIST_DEFAULT[str_type]
                else:
                    ret += CHOICE_LIST_ITEM[str_type] + "\\{:02X}".format(idx + 1)
                ret += arg
            ret += CHOICE_LIST_END[str_type]
            return ret
        if self.name == "G":
            if offset < 0:
                return self.arguments[lang.static_gender(static_args[offset]) - 1]
            ret = BEGIN_GENDER_CHOICE_LIST[str_type] + "\\{:02X}".format(0x80 + offset)
            for idx, arg in enumerate(self.arguments):
                if idx == len(self.arguments) - 1:
                    ret += CHOICE_LIST_DEFAULT[str_type]
                else:
                    ret += CHOICE_LIST_ITEM[str_type] + "\\{:02X}".format(idx + 1)
                ret += arg
            ret += CHOICE_LIST_END[str_type]
            return ret
        # Not reached
        raise ValueError("Unexpected string command '{}'".format(self.name))

    def get_type(self):
        if self.name in commands:
            if "ascii" in commands[self.name]:
                return "ascii"
            else:
                return "unicode"
        if self.name == "P" or self.name == "G":
            for arg in self.arguments:
                if not is_ascii_string(arg):
                    return "unicode"
        return "ascii"

    def is_important_command(self):
        if self.name in special_commands:
            return False
        return "size" in commands[self.name]

    def get_arg_size(self):
        return commands[self.name]["size"]


# Characters that are valid in hex numbers
VALID_HEX = "0123456789abcdefABCDEF"


def is_valid_hex(string):
    return all(c in VALID_HEX for c in string)


def validate_escapes(string, pos):
    """
    Validate that all escapes (starting with a backslash) are correct.
    When an invalid escape is encountered, an error is thrown

    @param string: String to validate
    @type string: C{str}

    @param pos: Position information
    @type pos: L{Position}
    """
    i = 0
    while i < len(string):
        # find next '\'
        i = string.find("\\", i)
        if i == -1:
            break

        if i + 1 >= len(string):
            raise generic.ScriptError("Unexpected end-of-line encountered after '\\'", pos)
        if string[i + 1] in ("\\", '"'):
            i += 2
        elif string[i + 1] == "U":
            if i + 5 >= len(string) or not is_valid_hex(string[i + 2 : i + 6]):
                raise generic.ScriptError("Expected 4 hexadecimal characters after '\\U'", pos)
            i += 6
        else:
            if i + 2 >= len(string) or not is_valid_hex(string[i + 1 : i + 3]):
                raise generic.ScriptError("Expected 2 hexadecimal characters after '\\'", pos)
            i += 3


class NewGRFString:
    """
    A string text in a language.

    @ivar string: String text.
    @type string: C{str}

    @ivar cases: Mapping of cases to ...
    @type cases: ???

    @ivar components: Split string text.
    @type components: C{list} of (C{str} or L{StringCommand})

    @ivar pos: Position of the string text.
    @type pos: L{Position}
    """

    def __init__(self, string, lang, pos):
        """
        Construct a L{NewGRFString}, and break down the string text into text literals and string commands.

        @param string: String text.
        @type  string: C{str}

        @param lang: Language containing this string.
        @type  lang: L{Language}

        @param pos: Position of the string text.
        @type  pos: L{Position}
        """
        validate_escapes(string, pos)
        self.string = string
        self.cases = {}
        self.components = []
        self.pos = pos
        idx = 0
        while idx < len(string):
            if string[idx] != "{":
                j = string.find("{", idx)
                if j == -1:
                    self.components.append(string[idx:])
                    break
                self.components.append(string[idx:j])
                idx = j

            start = idx + 1
            end = start
            cmd_pos = None
            if start >= len(string):
                raise generic.ScriptError("Expected '}' before end-of-line.", pos)
            if string[start].isdigit():
                while end < len(string) and string[end].isdigit():
                    end += 1
                if end == len(string) or string[end] != ":":
                    raise generic.ScriptError("Error while parsing position part of string command", pos)
                cmd_pos = int(string[start:end])
                start = end + 1
                end = start
            # Read the command name
            while end < len(string) and string[end] not in "} =.":
                end += 1
            command_name = string[start:end]
            if end < len(string) and string[end] == "=":
                command_name += "="
            if command_name not in commands and command_name not in special_commands:
                raise generic.ScriptError('Undefined command "{}"'.format(command_name), pos)
            if command_name in commands and "deprecated" in commands[command_name]:
                generic.print_warning(
                    generic.Warning.DEPRECATION,
                    "String code '{}' has been deprecated and will be removed soon".format(command_name),
                    pos,
                )
                del commands[command_name]["deprecated"]
            #
            command = StringCommand(command_name, cmd_pos, pos)
            if end >= len(string):
                raise generic.ScriptError("Missing '}}' from command \"{}\"".format(string[start:]), pos)
            if string[end] == ".":
                if command_name not in commands or "allow_case" not in commands[command_name]:
                    raise generic.ScriptError('Command "{}" can\'t have a case'.format(command_name), pos)
                case_start = end + 1
                end = case_start
                while end < len(string) and string[end] not in "} ":
                    end += 1
                case = string[case_start:end]
                if lang.cases is None or case not in lang.cases:
                    raise generic.ScriptError('Invalid case-name "{}"'.format(case), pos)
                command.case = lang.cases[case]
            if string[end] != "}":
                command.argument_is_assigment = string[end] == "="
                arg_start = end + 1
                end = string.find("}", end + 1)
                if end == -1 or not command.set_arguments(string[arg_start:end]):
                    raise generic.ScriptError("Missing '}}' from command \"{}\"".format(string[start:]), pos)
            command.validate_arguments(lang)
            if command_name == "G=" and self.components:
                raise generic.ScriptError("Set-gender command {G=} must be at the start of the string", pos)
            self.components.append(command)
            idx = end + 1

        if (
            len(self.components) > 0
            and isinstance(self.components[0], StringCommand)
            and self.components[0].name == "G="
        ):
            self.gender = self.components[0].arguments[0]
            if self.gender not in lang.genders:
                raise generic.ScriptError("Invalid gender name '{}'".format(self.gender), pos)
            self.components.pop(0)
        else:
            self.gender = None
        cmd_pos = 0
        for cmd in self.components:
            if not (isinstance(cmd, StringCommand) and cmd.is_important_command()):
                continue
            if cmd.str_pos is None:
                cmd.str_pos = cmd_pos
            cmd_pos = cmd.str_pos + 1

    def get_type(self):
        """
        Get the type of string text.

        @return: C{"unicode"} if Unicode is required for expressing the string text, else C{"ascii"}.
        @rtype:  C{str}
        """
        for comp in self.components:
            if isinstance(comp, StringCommand):
                if comp.get_type() == "unicode":
                    return "unicode"
            else:
                if not is_ascii_string(comp):
                    return "unicode"
        for case in self.cases.values():
            if case.get_type() == "unicode":
                return "unicode"
        return "ascii"

    def remove_non_default_commands(self):
        i = 0
        while i < len(self.components):
            comp = self.components[i]
            if isinstance(comp, StringCommand):
                if comp.name == "P" or comp.name == "G":
                    self.components[i] = comp.arguments[-1] if comp.arguments else ""
            i += 1

    def parse_string(self, str_type, lang, wanted_lang_id, static_args):
        """
        Convert the string text to output text.
        """
        ret = ""
        stack = [(idx, size) for idx, size in enumerate(self.get_command_sizes())]
        prev_command = None
        for comp in self.components:
            if isinstance(comp, StringCommand):
                next_command = stack[0] if stack else None
                ret += comp.parse_string(str_type, lang, wanted_lang_id, prev_command, stack, static_args)

                if (comp.name in commands) and comp.is_important_command():
                    prev_command = next_command
            else:
                ret += comp
        return ret

    def get_command_sizes(self):
        """
        Get the size of each string parameter.
        """
        sizes = {}
        for cmd in self.components:
            if not (isinstance(cmd, StringCommand) and cmd.is_important_command()):
                continue
            if cmd.str_pos in sizes:
                raise generic.ScriptError("Two or more string commands are using the same argument", self.pos)
            sizes[cmd.str_pos] = cmd.get_arg_size()
        sizes_list = []
        for idx in range(len(sizes)):
            if idx not in sizes:
                raise generic.ScriptError("String argument {:d} is not used".format(idx), self.pos)
            sizes_list.append(sizes[idx])
        return sizes_list

    def match_commands(self, other_string):
        return self.get_command_sizes() == other_string.get_command_sizes()


def isint(x, base=10):
    try:
        int(x, base)
        return True
    except ValueError:
        return False


NUM_PLURAL_FORMS = 14

CHOICE_LIST_ITEM = {"unicode": r"\UE09A\10", "ascii": r"\9A\10"}
CHOICE_LIST_DEFAULT = {"unicode": r"\UE09A\11", "ascii": r"\9A\11"}
CHOICE_LIST_END = {"unicode": r"\UE09A\12", "ascii": r"\9A\12"}
BEGIN_GENDER_CHOICE_LIST = {"unicode": r"\UE09A\13", "ascii": r"\9A\13"}
BEGIN_CASE_CHOICE_LIST = {"unicode": r"\UE09A\14", "ascii": r"\9A\14"}
BEGIN_PLURAL_CHOICE_LIST = {"unicode": r"\UE09A\15", "ascii": r"\9A\15"}
SET_STRING_GENDER = {"unicode": r"\UE09A\0E", "ascii": r"\9A\0E"}
STRING_SKIP = {"unicode": r"\UE085", "ascii": r"\85"}
STRING_ROTATE = {"unicode": r"\UE086", "ascii": r"\86"}
STRING_PUSH_WORD = {"unicode": r"\UE09A\03\20\20", "ascii": r"\9A\03\20\20"}
STRING_SELECT_CASE = {"unicode": r"\UE09A\0F", "ascii": r"\9A\0F"}


class Language:
    """
    @ivar default: Whether the language is the default language.
    @type default: C{bool}

    @ivar langid: Language id of the language, if known.
    @type langid: C{None} or C{int}

    @ivar plural: Plural type.
    @type plural: C{None} or C{int}

    @ivar genders:
    @type genders:

    @ivar gender_map:
    @type gender_map:

    @ivar cases:
    @type cases:

    @ivar case_map:
    @type case_map:

    @ivar strings: Language strings of the file.
    @type strings: C{dict} of
    """

    used_strings = []

    def __init__(self, default):
        self.default = default
        self.langid = None
        self.plural = None
        self.genders = None
        self.gender_map = {}
        self.cases = None
        self.case_map = {}
        self.strings = {}

    def get_num_plurals(self):
        if self.plural is None:
            return 0
        num_plurals = {
            0: 2,
            1: 1,
            2: 2,
            3: 3,
            4: 5,
            5: 3,
            6: 3,
            7: 3,
            8: 4,
            9: 2,
            10: 3,
            11: 2,
            12: 4,
            13: 4,
            14: 3,
        }
        return num_plurals[self.plural]

    def has_plural_pragma(self):
        return self.plural is not None

    def has_gender_pragma(self):
        return self.genders is not None

    def static_gender(self, expr):
        import nml.expression

        if isinstance(expr, nml.expression.StringLiteral):
            return len(self.genders)
        if not isinstance(expr, nml.expression.String):
            raise generic.ScriptError("{G} can only refer to a string argument")
        parsed = self.get_string(expr, self.langid)
        if parsed.find(SET_STRING_GENDER["ascii"]) == 0:
            return int(parsed[len(SET_STRING_GENDER["ascii"]) + 1 : len(SET_STRING_GENDER["ascii"]) + 3], 16)
        if parsed.find(SET_STRING_GENDER["unicode"]) == 0:
            return int(parsed[len(SET_STRING_GENDER["unicode"]) + 1 : len(SET_STRING_GENDER["unicode"]) + 3], 16)
        return len(self.genders)

    def static_plural_form(self, expr):
        # Return values are the same as "Plural index" here:
        # http://newgrf-specs.tt-wiki.net/wiki/StringCodes#Using_plural_forms
        val = expr.reduce_constant().value
        if self.plural == 0:
            return 1 if val == 1 else 2
        if self.plural == 1:
            return 1
        if self.plural == 2:
            return 1 if val in (0, 1) else 2
        if self.plural == 3:
            if val % 10 == 1 and val % 100 != 11:
                return 1
            return 2 if val == 0 else 3
        if self.plural == 4:
            if val == 1:
                return 1
            if val == 2:
                return 2
            if 3 <= val <= 6:
                return 3
            if 7 <= val <= 10:
                return 4
            return 5
        if self.plural == 5:
            if val % 10 == 1 and val % 100 != 11:
                return 1
            if 2 <= (val % 10) <= 9 and not 12 <= (val % 100) <= 19:
                return 2
            return 3
        if self.plural == 6:
            if val % 10 == 1 and val % 100 != 11:
                return 1
            if 2 <= (val % 10) <= 4 and not 12 <= (val % 100) <= 14:
                return 2
            return 3
        if self.plural == 7:
            if val == 0:
                return 1
            if 2 <= (val % 10) <= 4 and not 12 <= (val % 100) <= 14:
                return 2
            return 3
        if self.plural == 8:
            if val % 100 == 1:
                return 1
            if val % 100 == 2:
                return 2
            if val % 100 in (3, 4):
                return 3
            return 4
        if self.plural == 9:
            if val % 10 == 1 and val % 100 != 11:
                return 1
            return 2
        if self.plural == 10:
            if val == 1:
                return 1
            if 2 <= val <= 4:
                return 2
            return 3
        if self.plural == 11:
            if val % 10 in (0, 1, 3, 6, 7, 8):
                return 1
            return 2
        if self.plural == 12:
            if val == 1:
                return 1
            if val == 0 or 2 <= (val % 100) <= 10:
                return 2
            if 11 <= (val % 100) <= 19:
                return 3
            return 4
        if self.plural == 13:
            if val == 1 or val == 11:
                return 1
            if val == 2 or val == 12:
                return 2
            if (val >= 3 and val <= 10) or (val >= 13 and val <= 19):
                return 3
            return 4
        if self.plural == 14:
            if val == 1:
                return 1
            if val == 0 or 1 <= (val % 100) <= 19:
                return 2
            return 3
        raise AssertionError("Unknown plural type")

    def get_string(self, string, lang_id):
        """
        Lookup up a string by name/params and return the actual created string

        @param string: String object
        @type string: L{expression.String}

        @param lang_id: Language ID we are actually looking for.
                This may differ from the ID of this language,
                if the string is missing from the target language.
        @type lang_id: C{int}

        @return: The created string
        @rtype: C{str}
        """
        string_id = string.name.value
        assert isinstance(string_id, str)
        assert string_id in self.strings
        assert lang_id == self.langid or self.langid == DEFAULT_LANGUAGE

        if string_id not in Language.used_strings:
            Language.used_strings.append(string_id)

        str_type = self.strings[string_id].get_type()
        parsed_string = ""
        if self.strings[string_id].gender is not None:
            parsed_string += SET_STRING_GENDER[str_type] + "\\{:02X}".format(
                self.genders[self.strings[string_id].gender]
            )
        if len(self.strings[string_id].cases) > 0:
            parsed_string += BEGIN_CASE_CHOICE_LIST[str_type]
            for case_name, case_string in sorted(self.strings[string_id].cases.items()):
                case_id = self.cases[case_name]
                parsed_string += (
                    CHOICE_LIST_ITEM[str_type]
                    + "\\{:02X}".format(case_id)
                    + case_string.parse_string(str_type, self, lang_id, string.params)
                )
            parsed_string += CHOICE_LIST_DEFAULT[str_type]
        parsed_string += self.strings[string_id].parse_string(str_type, self, lang_id, string.params)
        if len(self.strings[string_id].cases) > 0:
            parsed_string += CHOICE_LIST_END[str_type]
        return parsed_string

    def handle_grflangid(self, data, pos):
        """
        Handle a 'grflangid' pragma.

        @param data: Data of the pragma.
        @type  data: C{str}
        """
        if self.langid is not None:
            raise generic.ScriptError("grflangid already set", pos)
        lang_text = data.strip()
        try:
            value = int(lang_text, 16)
        except ValueError:
            raise generic.ScriptError("Invalid grflangid {!r}".format(lang_text), pos)
        if value < 0 or value >= 0x7F:
            raise generic.ScriptError("Invalid grflangid", pos)
        self.langid = value

    def handle_plural(self, data, pos):
        """
        Handle a 'plural' pragma.

        @param data: Data of the pragma.
        @type  data: C{str}
        """
        if self.plural is not None:
            raise generic.ScriptError("plural form already set", pos)
        try:
            # Explicitly force base 10 like in OpenTTD's lang file
            value = int(data, 10)
        except ValueError:
            raise generic.ScriptError("Invalid plural form", pos)
        if value < 0 or value > NUM_PLURAL_FORMS:
            raise generic.ScriptError("Invalid plural form", pos)
        self.plural = value

    def handle_gender(self, data, pos):
        """
        Handle a 'gender' pragma.

        @param data: Data of the pragma.
        @type  data: C{str}
        """
        if self.genders is not None:
            raise generic.ScriptError("Genders already defined", pos)
        self.genders = {}
        for idx, gender in enumerate(data.split()):
            self.genders[gender] = idx + 1
            self.gender_map[gender] = []

    def handle_map_gender(self, data, pos):
        """
        Handle a 'map_gender' pragma.

        @param data: Data of the pragma.
        @type  data: C{str}
        """
        if self.genders is None:
            raise generic.ScriptError("##map_gender is not allowed before ##gender", pos)
        genders = data.split()
        if len(genders) != 2:
            raise generic.ScriptError("Invalid ##map_gender line", pos)
        if genders[0] not in self.genders:
            raise generic.ScriptError("Trying to map non-existing gender '{}'".format(genders[0]), pos)
        self.gender_map[genders[0]].append(genders[1])

    def handle_case(self, data, pos):
        """
        Handle a 'case' pragma.

        @param data: Data of the pragma.
        @type  data: C{str}
        """
        if self.cases is not None:
            raise generic.ScriptError("Cases already defined", pos)
        self.cases = {}
        for idx, case in enumerate(data.split()):
            self.cases[case] = idx + 1
            self.case_map[case] = []

    def handle_map_case(self, data, pos):
        """
        Handle a 'map_case' pragma.

        @param data: Data of the pragma.
        @type  data: C{str}
        """
        if self.cases is None:
            raise generic.ScriptError("##map_case is not allowed before ##case", pos)
        cases = data.split()
        if len(cases) != 2:
            raise generic.ScriptError("Invalid ##map_case line", pos)
        if cases[0] not in self.cases:
            raise generic.ScriptError("Trying to map non-existing case '{}'".format(cases[0]), pos)
        self.case_map[cases[0]].append(cases[1])

    def handle_text(self, string, case, value, pos):
        """
        Handle a text string definition.

        @param string: Name of the string.
        @type  string: C{str}

        @param case: The case being defined (optional).
        @type  case: C{str} or C{None}

        @param value: Value of the string.
        @type  value: C{str}
        """
        if not re.match("[A-Za-z_0-9]+$", string):
            raise generic.ScriptError('Invalid string name "{}"'.format(string), pos)

        if string in self.strings and case is None:
            raise generic.ScriptError('String name "{}" is used multiple times'.format(string), pos)

        if self.default:
            self.strings[string] = NewGRFString(value, self, pos)
            self.strings[string].remove_non_default_commands()
        else:
            if string not in default_lang.strings:
                generic.print_warning(
                    generic.Warning.GENERIC, 'String name "{}" does not exist in master file'.format(string), pos
                )
                return

            newgrf_string = NewGRFString(value, self, pos)
            if not default_lang.strings[string].match_commands(newgrf_string):
                generic.print_warning(
                    generic.Warning.GENERIC,
                    'String commands don\'t match with master file "{}"'.format(DEFAULT_LANGNAME),
                    pos,
                )
                return

            if case is None:
                self.strings[string] = newgrf_string
            else:
                if string not in self.strings:
                    generic.print_warning(generic.Warning.GENERIC, "String with case used before the base string", pos)
                    return
                if self.cases is None or case not in self.cases:
                    generic.print_warning(generic.Warning.GENERIC, 'Invalid case name "{}"'.format(case), pos)
                    return
                if case in self.strings[string].cases:
                    raise generic.ScriptError('String name "{}.{}" is used multiple times'.format(string, case), pos)
                if newgrf_string.gender:
                    generic.print_warning(
                        generic.Warning.GENERIC, "Case-strings can't set the gender, only the base string can", pos
                    )
                    return
                self.strings[string].cases[case] = newgrf_string

    def handle_string(self, line, pos):
        if len(line) == 0:
            # Silently ignore empty lines.
            return

        elif len(line) > 2 and line[:2] == "##" and not line[:3] == "###":
            # "##pragma" line, call relevant handler.
            if self.default:
                # Default language ignores all pragmas.
                return
            pragmas = {
                "##grflangid": self.handle_grflangid,
                "##plural": self.handle_plural,
                "##gender": self.handle_gender,
                "##map_gender": self.handle_map_gender,
                "##map_case": self.handle_map_case,
                "##case": self.handle_case,
            }
            try:
                pragma, value = line.split(" ", maxsplit=1)
                handler = pragmas[pragma]
            except (ValueError, KeyError):
                raise generic.ScriptError("Invalid pragma", pos)
            handler(value, pos)

        elif line[0] == "#":
            # Normal comment, ignore
            return

        else:
            # Must be a line defining a string.
            try:
                name, value = line.split(":", maxsplit=1)
                name = name.rstrip()
            except ValueError:
                raise generic.ScriptError("Line has no ':' delimiter", pos)

            if "." in name:
                name, case = name.rsplit(".", maxsplit=1)
                if not case:
                    raise generic.ScriptError("No case after '.' delimiter", pos)
            else:
                case = None

            if self.default and case is not None:
                # Ignore cases for the default language
                return

            self.handle_text(name, case, value, pos)


default_lang = Language(True)
default_lang.langid = DEFAULT_LANGUAGE
langs = []


def parse_file(filename, default):
    """
    Read and parse a single language file.

    @param filename: The filename of the file to parse.
    @type  filename: C{str}

    @param default: True iff this is the default language.
    @type  default: C{bool}
    """
    lang = Language(False)
    try:
        with open(generic.find_file(filename), "r", encoding="utf-8") as fh:
            for idx, line in enumerate(fh):
                pos = generic.LinePosition(filename, idx + 1)
                line = line.rstrip("\n\r").lstrip("\ufeff")
                # The default language is processed twice here. Once as fallback langauge
                # and once as normal language.
                if default:
                    default_lang.handle_string(line, pos)
                lang.handle_string(line, pos)
    except UnicodeDecodeError:
        pos = generic.LanguageFilePosition(filename)
        if default:
            raise generic.ScriptError("The default language file contains non-utf8 characters.", pos)
        generic.print_warning(
            generic.Warning.GENERIC, "Language file contains non-utf8 characters. Ignoring (part of) the contents.", pos
        )
    except generic.ScriptError as err:
        if default:
            raise
        generic.print_warning(generic.Warning.GENERIC, err.value, err.pos)
    else:
        if lang.langid is None:
            generic.print_warning(
                generic.Warning.GENERIC,
                "Language file does not contain a ##grflangid pragma",
                generic.LanguageFilePosition(filename),
            )
        else:
            for lng in langs:
                if lng[0] == lang.langid:
                    msg = "Language file has the same ##grflangid (with number {:d}) as another language file".format(
                        lang.langid
                    )
                    raise generic.ScriptError(msg, generic.LanguageFilePosition(filename))
            langs.append((lang.langid, lang))


def read_lang_files(lang_dir, default_lang_file):
    """
    Read the language files containing the translations for string constants
    used in the NML specification.

    @param lang_dir: Name of the directory containing the language files.
    @type  lang_dir: C{str}

    @param default_lang_file: Filename of the language file that has the
                              default translation which will be used as
                              fallback for other languages.
    @type  default_lang_file: C{str}
    """
    global DEFAULT_LANGNAME

    DEFAULT_LANGNAME = default_lang_file
    if not os.path.exists(lang_dir + os.sep + default_lang_file):
        generic.print_warning(
            generic.Warning.GENERIC,
            'Default language file "{}" doesn\'t exist'.format(os.path.join(lang_dir, default_lang_file)),
        )
        return
    parse_file(lang_dir + os.sep + default_lang_file, True)
    for filename in glob.glob(lang_dir + os.sep + "*.lng"):
        if filename.endswith(default_lang_file):
            continue
        parse_file(filename, False)
    langs.sort()


def list_unused_strings():
    for string in default_lang.strings:
        if string in Language.used_strings:
            continue
        generic.print_warning(generic.Warning.GENERIC, 'String "{}" is unused'.format(string))
