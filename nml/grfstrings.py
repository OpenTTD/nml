import os, codecs, re, glob
from nml import generic

def utf8_get_size(char):
    if char < 128: return 1
    if char < 2048: return 2
    if char < 65536: return 3
    return 4

DEFAULT_LANGUAGE = 0x7F

def is_valid_string(string):
    return string in default_lang.strings

def can_use_ascii(string):
    i = 0
    while i < len(string):
        if string[i] != '\\':
            if ord(string[i]) >= 0x80:
                return False
            i += 1
        else:
            if string[i+1] in ('\\', 'n', '"'):
                i += 2
            elif string[i+1] == 'U':
                return False
                i += 6
            else:
                i += 3
    return True

def get_string_size(string, final_zero = True, force_ascii = False):
    size = 0
    if final_zero: size += 1
    if not can_use_ascii(string):
        if force_ascii:
            raise generic.ScriptError("Expected ascii string but got a unicode string")
        size += 2
    i = 0
    while i < len(string):
        if string[i] != '\\':
            size += utf8_get_size(ord(string[i]))
            i += 1
        else:
            if string[i+1] in ('\\', 'n', '"'):
                size += 1
                i += 2
            elif string[i+1] == 'U':
                size += utf8_get_size(int(string[i+2:i+6], 16))
                i += 6
            else:
                size += 1
                i += 3
    return size

def get_translation(string, lang_id = DEFAULT_LANGUAGE):
    """
    Get the translation of a given string in a certain language. If there is no
    translation available in the given language return the default translation.

    @param string: the string to get the translation for.
    @type  string: L{expression.String}

    @param lang_id: The language id of the language to translate the string into.
    @type  lang_id: C{int}

    @return: Translation of the given string in the given language.
    @rtype:  C{unicode}
    """
    for lang_pair in langs:
        langid, lang = lang_pair
        if langid != lang_id: continue
        if string.name.value not in lang.strings: break
        return lang.get_string(string.name.value)
    return default_lang.get_string(string.name.value)

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
        if string.name.value in lang.strings and lang.get_string(string.name.value) != default_lang.get_string(string.name.value):
            translations.append(langid)
    return translations

commands = {
'':               {'unicode': r'\0D',       'ascii': r'\0D',    'num_params': 0},
'{':              {'unicode': r'{',         'ascii': r'{',      'num_params': 0},
'NBSP':           {'unicode': r'\U00A0',    'ascii': r'\A0',    'num_params': 0},
'COPYRIGHT':      {'unicode': r'\U00A9',    'ascii': r'\A9',    'num_params': 0},
'TINYFONT':       {'unicode': r'\0E',       'ascii': r'\0E',    'num_params': 0},
'BIGFONT':        {'unicode': r'\0F',       'ascii': r'\0F',    'num_params': 0},
'DWORD_S':        {'unicode': r'\UE07B',    'ascii': r'\7B',    'num_params': 0},
'PARAM':          {'unicode': r'\UE07B',    'ascii': r'\7B',    'num_params': 0},
'WORD_S':         {'unicode': r'\UE07C',    'ascii': r'\7C',    'num_params': 0},
'BYTE_S':         {'unicode': r'\UE07D',    'ascii': r'\7D',    'num_params': 0},
'WORD_U':         {'unicode': r'\UE07E',    'ascii': r'\7E',    'num_params': 0},
'CURRENCY':       {'unicode': r'\UE07F',    'ascii': r'\7F',    'num_params': 0},
'STRING':         {'unicode': r'\UE080',    'ascii': r'\80',    'num_params': 0, 'allow_case': True},
'DATE_LONG':      {'unicode': r'\UE082',    'ascii': r'\82',    'num_params': 0},
'DATE_TINY':      {'unicode': r'\UE083',    'ascii': r'\83',    'num_params': 0},
'VELOCITY':       {'unicode': r'\UE084',    'ascii': r'\84',    'num_params': 0},
'POP_WORD':       {'unicode': r'\UE085',    'ascii': r'\85',    'num_params': 0},
'ROTATE':         {'unicode': r'\UE086',    'ascii': r'\86',    'num_params': 0},
'VOLUME':         {'unicode': r'\UE087',    'ascii': r'\87',    'num_params': 0},
'CURRENCY_QWORD': {'unicode': r'\UE09A\01', 'ascii': r'\9A\01', 'num_params': 0},
'PUSH_WORD':      {'unicode': r'\UE09A\03', 'ascii': r'\9A\03', 'num_params': 1, 'param_size': 2},
'UNPRINT':        {'unicode': r'\UE09A\04', 'ascii': r'\9A\04', 'num_params': 1, 'param_size': 1},
'BYTE_HEX':       {'unicode': r'\UE09A\06', 'ascii': r'\9A\06', 'num_params': 0},
'WORD_HEX':       {'unicode': r'\UE09A\07', 'ascii': r'\9A\07', 'num_params': 0},
'DWORD_HEX':      {'unicode': r'\UE09A\08', 'ascii': r'\9A\08', 'num_params': 0},
'QWORD_HEX':      {'unicode': r'\UE09A\0B', 'ascii': r'\9A\0B', 'num_params': 0},
'BLUE':           {'unicode': r'\UE088',    'ascii': r'\88',    'num_params': 0},
'SILVER':         {'unicode': r'\UE089',    'ascii': r'\89',    'num_params': 0},
'GOLD':           {'unicode': r'\UE08A',    'ascii': r'\8A',    'num_params': 0},
'RED':            {'unicode': r'\UE08B',    'ascii': r'\8B',    'num_params': 0},
'PURPLE':         {'unicode': r'\UE08C',    'ascii': r'\8C',    'num_params': 0},
'LTBROWN':        {'unicode': r'\UE08D',    'ascii': r'\8D',    'num_params': 0},
'ORANGE':         {'unicode': r'\UE08E',    'ascii': r'\8E',    'num_params': 0},
'GREEN':          {'unicode': r'\UE08F',    'ascii': r'\8F',    'num_params': 0},
'YELLOW':         {'unicode': r'\UE090',    'ascii': r'\90',    'num_params': 0},
'DKGREEN':        {'unicode': r'\UE091',    'ascii': r'\91',    'num_params': 0},
'CREAM':          {'unicode': r'\UE092',    'ascii': r'\92',    'num_params': 0},
'BROWN':          {'unicode': r'\UE093',    'ascii': r'\93',    'num_params': 0},
'WHITE':          {'unicode': r'\UE094',    'ascii': r'\94',    'num_params': 0},
'LTBLUE':         {'unicode': r'\UE095',    'ascii': r'\95',    'num_params': 0},
'GRAY':           {'unicode': r'\UE096',    'ascii': r'\96',    'num_params': 0},
'DKBLUE':         {'unicode': r'\UE097',    'ascii': r'\97',    'num_params': 0},
'BLACK':          {'unicode': r'\UE098',    'ascii': r'\98',    'num_params': 0},
'TRAIN':          {'unicode': r'\UE0B4',    'ascii': r'\B4',    'num_params': 0},
'LORRY':          {'unicode': r'\UE0B5',    'ascii': r'\B5',    'num_params': 0},
'BUS':            {'unicode': r'\UE0B6',    'ascii': r'\B6',    'num_params': 0},
'PLANE':          {'unicode': r'\UE0B7',    'ascii': r'\B7',    'num_params': 0},
'SHIP':           {'unicode': r'\UE0B8',    'ascii': r'\B8',    'num_params': 0},
}

special_commands = [
'P',
'G',
]

def read_extra_commands(custom_tags_file):
    """
    @param custom_tags_file: Filename of the custom tags file.
    @type  custom_tags_file: C{str}
    """
    global commands
    if not os.access(custom_tags_file, os.R_OK):
        #Failed to open custom_tags.txt, ignore this
        return
    for line in codecs.open(custom_tags_file, "r", "utf-8"):
        line = line.strip()
        if len(line) == 0 or line[0] == "#":
            pass
        else:
            i = line.index(':')
            name = line[:i].strip()
            value = line[i+1:]
            if name in commands:
                generic.print_warning('Warning: overwriting existing tag "' + name + '"')
            commands[name] = {'unicode': value, 'num_params': 0}
            if can_use_ascii(value):
                commands[name]['ascii'] = value


class StringCommand(object):
    def __init__(self, name):
        assert name in commands or name in special_commands
        self.name = name
        self.case = None
        self.arguments = None

    def set_arguments(self, arg_string):
        self.arguments = []
        start = -1
        cur = 0
        quoted = False
        whitespace = " \t"
        while cur < len(arg_string):
            if start != -1:
                if (quoted and arg_string[cur] == '"') or (not quoted and arg_string[cur] in whitespace):
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

    def parse_string(self, str_type):
        if self.name in commands:
            return commands[self.name][str_type]
        assert self.name in special_commands
        if self.name == 'P':
            ret = BEGIN_PLURAL_CHOICE_LIST[str_type] + '\\' + generic.to_hex(0x80, 2)
            for idx, arg in enumerate(self.arguments):
                if idx == len(self.arguments) - 1:
                    ret += CHOICE_LIST_DEFAULT[str_type]
                else:
                    ret += CHOICE_LIST_ITEM[str_type] + '\\' + generic.to_hex(idx + 1, 2)
                ret += arg
            ret += CHOICE_LIST_END[str_type]
            return ret
        if self.name == 'G':
            ret = BEGIN_GENDER_CHOICE_LIST[str_type] + '\\' + generic.to_hex(0x80, 2)
            for idx, arg in enumerate(self.arguments):
                if idx == len(self.arguments) - 1:
                    ret += CHOICE_LIST_DEFAULT[str_type]
                else:
                    ret += CHOICE_LIST_ITEM[str_type] + '\\' + generic.to_hex(idx + 1, 2)
                ret += arg
            ret += CHOICE_LIST_END[str_type]
            return ret

    def get_type(self):
        if self.name in commands:
            if 'ascii' in commands[self.name]: return 'ascii'
            else: return 'unicode'
        if self.name == 'P':
            for arg in self.arguments:
                if not can_use_ascii(arg): return 'unicode'
            return 'ascii'

class NewGRFString(object):
    def __init__(self, string, lang, strip_choice_lists, pos):
        self.string = string
        self.cases = {}
        self.components = []
        parsed_string = None
        idx = 0
        while idx < len(string):
            if string[idx] != '{':
                if parsed_string is None: parsed_string = u""
                parsed_string += string[idx]
            else:
                if parsed_string is not None:
                    self.components.append(parsed_string)
                    parsed_string = None
                start = idx + 1
                end = start
                #Read the command name
                while end < len(string) and string[end] not in '} =.': end += 1
                command_name = string[start:end]
                if command_name not in commands and command_name not in special_commands:
                    raise generic.ScriptError("Undefined command \"%s\"" % command_name, pos)
                #
                command = StringCommand(command_name)
                if string[end] == '.':
                    if 'allow_case' not in commands[command_name]:
                        raise generic.ScriptError("Command \"%s\" can't have a case" % command_name, pos)
                    case_start = end + 1
                    end = case_start 
                    while end < len(string) and string[end] not in '} ': end += 1
                    case = string[case_start:end]
                    if lang.cases is None or case not in lang.cases:
                        raise generic.ScriptError("Invalid case-name \"%s\"" % case, pos)
                    command.case = lang.cases[case]
                if end >= len(string):
                    raise generic.ScriptError("Missing '}' from command \"%s\"" % string[start:], pos)
                if string[end] != '}':
                    command.argument_is_assigment = string[end] == '='
                    arg_start = end + 1
                    while True:
                        end += 1
                        if end >= len(string):
                            raise generic.ScriptError("Missing '}' from command \"%s\"" % string[start:], pos)
                        if string[end] == '}': break
                    if not command.set_arguments(string[arg_start:end]):
                        raise generic.ScriptError("Missing '}' from command \"%s\"" % string[start:], pos)
                self.components.append(command)
                idx = end
            idx += 1
        if parsed_string is not None: self.components.append(parsed_string)

    def get_type(self):
        for comp in self.components:
            if isinstance(comp, StringCommand):
                if comp.get_type() == 'unicode':
                    return 'unicode'
            else:
                if not can_use_ascii(comp): return 'unicode'
        for case in self.cases:
            if case.get_type() == 'unicode':
                return 'unicode'
        return 'ascii'

    def remove_non_default_commands(self):
        i = 0
        while i < len(self.components):
            comp = self.components[i]
            if isinstance(comp, StringCommand):
                if comp.name == 'P' or comp.name == 'G':
                    self.components[i] = comp.arguments[-1]
            i += 1

    def parse_string(self, str_type):
        ret = ""
        for comp in self.components:
            if isinstance(comp, StringCommand):
                ret += comp.parse_string(str_type)
            else:
                ret += comp
        return ret

    def match_commands(self, other_string):
        #TODO: check if the commands match the default language
        return True

def isint(x, base = 10):
    try:
        a = int(x, base)
        return True
    except ValueError:
        return False

NUM_PLURAL_FORMS = 12

CHOICE_LIST_ITEM         = {'unicode': r'\UE09A\10', 'ascii': r'\9A\10'}
CHOICE_LIST_DEFAULT      = {'unicode': r'\UE09A\11', 'ascii': r'\9A\11'}
CHOICE_LIST_END          = {'unicode': r'\UE09A\12', 'ascii': r'\9A\12'}
BEGIN_GENDER_CHOICE_LIST = {'unicode': r'\UE09A\13', 'ascii': r'\9A\13'}
BEGIN_CASE_CHOICE_LIST   = {'unicode': r'\UE09A\14', 'ascii': r'\9A\14'}
BEGIN_PLURAL_CHOICE_LIST = {'unicode': r'\UE09A\15', 'ascii': r'\9A\15'}

class Language:
    def __init__(self):
        self.langid = None
        self.plural = None
        self.genders = None
        self.gender_map = {}
        self.cases = None
        self.case_map = {}
        self.strings = {}

    def get_string(self, string):
        assert isinstance(string, basestring)
        assert string in self.strings
        str_type = self.strings[string].get_type()
        parsed_string = ""
        if len(self.strings[string].cases) > 0:
            parsed_string += BEGIN_CASE_CHOICE_LIST[str_type]
            for case_name, case_string in self.strings[string].cases.iteritems():
                case_id = self.cases[case_name]
                parsed_string += CHOICE_LIST_ITEM[str_type] + '\\' + generic.to_hex(case_id, 2) + case_string.parse_string(str_type)
            parsed_string += CHOICE_LIST_DEFAULT[str_type]
        parsed_string += self.strings[string].parse_string(str_type)
        if len(self.strings[string].cases) > 0:
            parsed_string += CHOICE_LIST_END[str_type]
        return parsed_string

    def handle_pragma(self, line, pos):
        if line[:10] == "grflangid ":
            if self.langid is not None:
                raise generic.ScriptError("grflangid already set", pos)
            try:
                value = int(line[10:], 16)
            except ValueError:
                raise generic.ScriptError("Invalid grflangid", pos)
            if value < 0 or value >= 0x7F:
                raise generic.ScriptError("Invalid grflangid", pos)
            self.langid = value
        elif line[:7] == "plural ":
            if self.plural is not None:
                raise generic.ScriptError("plural form already set", pos)
            try:
                value = int(line[7:], 16)
            except ValueError:
                raise generic.ScriptError("Invalid plural form", pos)
            if value < 0 or value > NUM_PLURAL_FORMS:
                raise generic.ScriptError("Invalid plural form", pos)
            self.plural = value
        elif line[:7] == "gender ":
            if self.genders is not None:
                raise generic.ScriptError("Genders already defined", pos)
            self.genders = {}
            for idx, gender in enumerate(line[7:].split()):
                self.genders[gender] = idx + 1
                self.gender_map[gender] = []
        elif line[:11] == "map_gender ":
            if self.genders is None:
                raise generic.ScriptError("##map_gender is not allowed before ##gender", pos)
            genders = line[11:].split()
            if len(genders) != 2:
                raise generic.ScriptError("Invalid ##map_gender line", pos)
            if genders[0] not in self.genders: 
                raise generic.ScriptError("Trying to map non-existing gender '%s'" % genders[0], pos)
            self.gender_map[genders[0]].append(genders[1])
        elif line[:5] == "case ":
            if self.cases is not None:
                raise generic.ScriptError("Cases already defined", pos)
            self.cases = {}
            for idx, case in enumerate(line[5:].split()):
                self.cases[case] = idx + 1
                self.case_map[case] = []
        else:
            raise generic.ScriptError("Invalid pragma", pos)

    def handle_string(self, line, default, pos):
        if len(line) == 0: return

        if line[0] == '#':
            if len(line) > 2 and line[1] == '#' and line[2] != '#' and not default: self.handle_pragma(line[2:], pos)
            return

        s = line.find(':')
        if s == -1:
            raise generic.ScriptError("Line has no ':' delimeter", pos)

        string = line[:s].strip()
        value = line[s + 1:]
        case_pos = string.find('.')

        if case_pos == -1:
            case = None
        else:
            # Ignore cases for the default language
            if default: return
            case = string[case_pos + 1:]
            string = string[:case_pos]

        if string in self.strings and case is None:
            raise generic.ScriptError("String name \"%s\" is used multiple times" % string, pos)

        if default:
            self.strings[string] = NewGRFString(value, self, True, pos)
            self.strings[string].remove_non_default_commands()
        else:
            if string not in default_lang.strings:
                generic.print_warning("String name \"%s\" does not exist in master file" % string, pos)
                return

            newgrf_string = NewGRFString(value, self, False, pos)
            if not default_lang.strings[string].match_commands(newgrf_string):
                generic.print_warning("String commands don't match with english.lng", pos)
                return

            if case is None:
                self.strings[string] = newgrf_string
            else:
                if string not in self.strings:
                    generic.print_warning("String with case used before the base string", pos)
                    return
                if self.cases is None or case not in self.cases:
                    generic.print_warning("Invalid case name \"%s\"" % case, pos)
                    return
                if case in self.strings[string].cases:
                    raise generic.ScriptError("String name \"%s.%s\" is used multiple times" % (string, case), pos)
                self.strings[string].cases[case] = newgrf_string


default_lang = Language()
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
    lang = Language()
    try:
        with codecs.open(filename, "r", "utf-8") as f:
            for idx, line in enumerate(f):
                pos = generic.LinePosition(filename, idx + 1)
                if default: default_lang.handle_string(line.rstrip('\n\r'), True, pos)
                lang.handle_string(line.rstrip('\n\r'), False, pos)
    except UnicodeDecodeError:
        if default:
            raise generic.ScriptError("The default language file (\"%s\") contains non-utf8 characters." % filename)
        generic.print_warning("Language file \"%s\" contains non-utf8 characters. Ignoring (part of) the contents" % filename)
    except generic.ScriptError as err:
        if default: raise
        generic.print_warning("Error in language file \"%s\": %s" % (filename, err))
    else:
        if lang.langid is None:
            generic.print_warning("Language file \"%s\" does not contain a ##grflangid pragma" % filename)
        else:
            langs.append((lang.langid, lang))

def read_lang_files(lang_dir):
    """
    Read the language files containing the translations for string constants used in the NML specification.

    @param lang_dir: Name of the directory containing the language files.
    @type  lang_dir: C{str}
    """
    DEFAULT_LANGUAGE_FILE = "english.lng"
    if not os.path.exists(lang_dir + os.sep + DEFAULT_LANGUAGE_FILE):
        raise generic.ScriptError("Default language file \"%s\" doesn't exist" % (lang_dir + os.sep + DEFAULT_LANGUAGE_FILE))
    parse_file(lang_dir + os.sep + DEFAULT_LANGUAGE_FILE, True)
    for filename in glob.glob(lang_dir + os.sep + "*.lng"):
        if filename.endswith(DEFAULT_LANGUAGE_FILE): continue
        parse_file(filename, False)
    langs.sort()
