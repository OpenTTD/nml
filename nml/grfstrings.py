import os, codecs, re, glob
from nml import generic

grf_strings = {}

def get_translation(string, lang = 0x7F):
    global grf_strings
    if string not in grf_strings:
        raise generic.ScriptError('String "%s" is not translatable' % string)
    def_trans = None
    for translation in grf_strings[string]:
        if translation['lang'] == lang:
            return translation['text']
        if translation['lang'] == 0x7F:
            def_trans = translation['text']
    return def_trans

def utf8_get_size(char):
    if char < 128: return 1
    if char < 2048: return 2
    if char < 65536: return 3
    return 4

def get_string_size(string):
    size = 0
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

escapes = {
'':               {'escape': r'\0D',    'num_params': 0},
'{':              {'escape': r'{',      'num_params': 0},
'TINYFONT':       {'escape': r'\0E',    'num_params': 0},
'BIGFONT':        {'escape': r'\0F',    'num_params': 0},
'DWORD_S':        {'escape': r'\UE07B', 'num_params': 0},
'WORD_S':         {'escape': r'\UE07C', 'num_params': 0},
'BYTE_S':         {'escape': r'\UE07D', 'num_params': 0},
'WORD_U':         {'escape': r'\UE07E', 'num_params': 0},
'CURRENCY':       {'escape': r'\UE07F', 'num_params': 0},
'STRING':         {'escape': r'\UE080', 'num_params': 0},
'DATE_LONG':      {'escape': r'\UE082', 'num_params': 0},
'DATE_TINY':      {'escape': r'\UE083', 'num_params': 0},
'VELOCITY':       {'escape': r'\UE084', 'num_params': 0},
'POP_WORD':       {'escape': r'\UE085', 'num_params': 0},
'ROTATE':         {'escape': r'\UE086', 'num_params': 0},
'VOLUME':         {'escape': r'\UE087', 'num_params': 0},
'CURRENCY_QWORD': {'escape': r'\UE09A\01', 'num_params': 0},
'PUSH_WORD':      {'escape': r'\UE09A\03', 'num_params': 1, 'param_size': 2},
'UNPRINT':        {'escape': r'\UE09A\04', 'num_params': 1, 'param_size': 1},
'BYTE_HEX':       {'escape': r'\UE09A\06', 'num_params': 0},
'WORD_HEX':       {'escape': r'\UE09A\07', 'num_params': 0},
'DWORD_HEX':      {'escape': r'\UE09A\08', 'num_params': 0},
'QWORD_HEX':      {'escape': r'\UE09A\0B', 'num_params': 0},
'BLUE':           {'escape': r'\UE088', 'num_params': 0},
'LIGHT_GRAY':     {'escape': r'\UE089', 'num_params': 0},
'LIGHT_ORANGE':   {'escape': r'\UE08A', 'num_params': 0},
'RED':            {'escape': r'\UE08B', 'num_params': 0},
'PURPLE':         {'escape': r'\UE08C', 'num_params': 0},
'GRAY_GREEN':     {'escape': r'\UE08D', 'num_params': 0},
'ORANGE':         {'escape': r'\UE08E', 'num_params': 0},
'GREEN':          {'escape': r'\UE08F', 'num_params': 0},
'YELLOW':         {'escape': r'\UE090', 'num_params': 0},
'LIGHT_GREEN':    {'escape': r'\UE091', 'num_params': 0},
'RED_BROWN':      {'escape': r'\UE092', 'num_params': 0},
'BROWN':          {'escape': r'\UE093', 'num_params': 0},
'WHITE':          {'escape': r'\UE094', 'num_params': 0},
'LIGHT_BLUE':     {'escape': r'\UE095', 'num_params': 0},
'DARK_GRAY':      {'escape': r'\UE096', 'num_params': 0},
'MAUVE':          {'escape': r'\UE097', 'num_params': 0},
'BLACK':          {'escape': r'\UE098', 'num_params': 0},
'TRAIN':          {'escape': r'\UE0B4', 'num_params': 0},
'LORRY':          {'escape': r'\UE0B5', 'num_params': 0},
'BUS':            {'escape': r'\UE0B6', 'num_params': 0},
'PLANE':          {'escape': r'\UE0B7', 'num_params': 0},
'SHIP':           {'escape': r'\UE0B8', 'num_params': 0},
}

def read_extra_commands(custom_tags_file):
    """
    @param custom_tags_file: Filename of the custom tags file.
    @type  custom_tags_file: C{str}
    """
    global escapes
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
            if name in escapes:
                print 'Warning: overwriting existing tag "' + name + '"'
            escapes[name] = {'escape': value, 'num_params': 0}

def parse_command(command):
    global escapes
    match = re.match(r'^([a-zA-Z_]*)(( \d+)*)$', command)
    if match is None: raise generic.ScriptError("Failed to parse string command: '" + command + "'")
    cmd_name = match.group(1)
    arguments = match.group(2).split()
    if cmd_name not in escapes: raise generic.ScriptError("Unknown string command: '" + cmd_name + "'")
    escape = escapes[cmd_name]
    if escape['num_params'] != len(arguments): raise generic.ScriptError("Wrong number of arguments in command: '" + command + "'")
    ret = escape['escape']
    if len(arguments) > 0:
        ret += '" '
        for arg in arguments:
            if escape['param_size'] == 1: ret += hex(arg)[2:].upper() + ' '
            elif escape['param_size'] == 2: ret += '\\w' + arg + ' '
        ret += '"'
    return ret

def parse_grf_string(orig_string):
    ret = ''
    ignore = 0
    special_chars = {r'"': r'\"', r'\\': r'\\\\'}
    for i in range(len(orig_string)):
        if ignore > 0:
            ignore = ignore - 1
            continue
        c = orig_string[i]
        if c == '{':
            has_end = False
            for j in range(i + 1, len(orig_string)):
                if orig_string[j] == '}':
                    has_end = True
                    ret += parse_command(orig_string[i+1:j])
                    ignore = j - i
                    break
            if not has_end: raise generic.ScriptError("Command block without ending '}'")
        elif c in special_chars:
            ret += special_chars[c]
        else:
            ret += c
    return ret

def read_lang_files(lang_dir):
    """
    @param lang_dir: Name of the direcotry containing the language files.
    @type  lang_dir: C{str}
    """
    for filename in glob.glob(lang_dir + os.sep + "*.lng"):
        lang = -1
        for line in codecs.open(filename, "r", "utf-8"):
            line = line.strip()
            if len(line) == 0 or line[0] == "#":
                pass
            elif line[:6] == "lang: ":
                assert lang == -1, "Only one 'lang:' line allowed per language file"
                lang = int(line[6:8], 16)
            else:
                assert lang != -1, "Language id not set"
                i = line.index(':')
                name = line[:i].strip()
                value = line[i+1:]
                if not name in grf_strings:
                    grf_strings[name] = []
                grf_strings[name].append({'lang': lang, 'text': parse_grf_string(value)})
