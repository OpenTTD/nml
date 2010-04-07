import ast
from generic import *
from grfstrings import grf_strings
from action6 import *
from actionD import *

class ActionB:
    def __init__(self, severity, lang, msg, data, param1, param2):
        self.severity = severity
        self.lang = lang
        self.msg = msg
        self.data = data
        self.param1 = param1
        self.param2 = param2
    
    def write(self, file):
        file.write("-1 * 0 0B ")
        self.severity.write(file, 1)
        print_bytex(file, self.lang)
        if isinstance(self.msg, int):
            print_bytex(file, self.msg)
        else:
            print_bytex(file, 0xFF)
            print_string(file, self.msg)
        if self.data != None:
            print_string(file, self.data)
            if self.param1 != None:
                print_bytex(file, self.param1)
                if self.param2 != None:
                    print_bytex(file, self.param2)
        file.write("\n\n")
    
    def skip_action7(self):
        return False
    
    def skip_action9(self):
        return True
    
    def skip_needed(self):
        return True

default_error_msg = {
    'REQUIRES_TTDPATCH' : 0,
    'REQUIRES_DOS_WINDOWS' : 1,
    'USED_WITH' : 2,
    'INVALID_PARAMETER' : 3,
    'MUST_LOAD_BEFORE' : 4,
    'MUST_LOAD_AFTER' : 5,
    'REQUIRES_OPENTTD' : 6,
}

def get_translation(string, lang):
    global grf_strings
    assert string in grf_strings
    def_trans = None
    for translation in grf_strings[string]:
        if translation['lang'] == lang:
            return translation['text']
        if translation['lang'] == 0x7F:
            def_trans = translation['text']
    return def_trans

def parse_error_block(error):
    global free_parameters, default_error_msg, grf_strings
    free_parameters_backup = free_parameters[:]
    action_list = []
    action6 = Action6()
    
    if isinstance(error.severity, ast.ConstantNumeric):
        severity = error.severity
    elif isinstance(error.severity, ast.Parameter) and isinstance(error.severity.num, ast.ConstantNumeric):
        action6.modify_bytes(error.severity.num.value, 1, 1)
        severity = ast.ConstantNumeric(0)
    else:
        tmp_param, tmp_param_actions = get_tmp_parameter(id)
        action_list.extend(tmp_param_actions)
        action6.modify_bytes(tmp_param, 1, 1)
        severity = ast.ConstantNumeric(0)
    
    langs = [0x7F]
    if error.msg in default_error_msg:
        custom_msg = False
        msg = default_error_msg[error.msg]
    else:
        custom_msg = True
        for translation in grf_strings[error.msg]:
            langs.append(translation['lang'])
    
    if error.data != None:
        for translation in grf_strings[error.data]:
            langs.append(translation['lang'])
    
    langs = set(langs)
    for lang in langs:
        if custom_msg:
            msg = get_translation(error.msg, lang)
        data = None if error.data == None else get_translation(error.data, lang)
        action_list.append(ActionB(severity, lang, msg, data, None, None))
    
    free_parameters = free_parameters_backup
    return action_list
