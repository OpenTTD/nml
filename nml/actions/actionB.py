from nml.expression import *
from nml import generic
from nml.grfstrings import grf_strings, get_translation, get_string_size
from action6 import *
from actionD import *

class ActionB(object):
    def __init__(self, severity, lang, msg, data, param1, param2):
        self.severity = severity
        self.lang = lang
        self.msg = msg
        self.data = data
        self.param1 = param1
        self.param2 = param2

    def prepare_output(self):
        pass

    def write(self, file):
        size = 4
        if not isinstance(self.msg, int): size += get_string_size(self.msg) + 3
        if self.data is not None:
            size += get_string_size(self.data) + 3
            if self.param1 is not None:
                size += 1
                if self.param2 is not None:
                    size += 1

        file.print_sprite_size(size)
        file.print_bytex(0x0B)
        self.severity.write(file, 1)
        file.print_bytex(self.lang)
        if isinstance(self.msg, int):
            file.print_bytex(self.msg)
        else:
            file.print_bytex(0xFF)
            file.print_string(self.msg)
        if self.data is not None:
            file.print_string(self.data)
            if self.param1 is not None:
                self.param1.write(file, 1)
                if self.param2 is not None:
                    self.param2.write(file, 1)
        file.newline()
        file.newline()

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

error_severity = {
    'NOTICE'  : 0,
    'WARNING' : 1,
    'ERROR'   : 2,
    'FATAL'   : 3,
}

def parse_error_block(error):
    global free_parameters, default_error_msg, grf_strings
    free_parameters_backup = free_parameters[:]
    action_list = []
    action6 = Action6()

    if isinstance(error.severity, ConstantNumeric):
        severity = error.severity
    elif isinstance(error.severity, Parameter) and isinstance(error.severity.num, ConstantNumeric):
        action6.modify_bytes(error.severity.num.value, 1, 1)
        severity = ConstantNumeric(0)
    else:
        tmp_param, tmp_param_actions = get_tmp_parameter(error.severity)
        action_list.extend(tmp_param_actions)
        action6.modify_bytes(tmp_param, 1, 1)
        severity = ConstantNumeric(0)

    if not isinstance(error.msg, Identifier):
        raise generic.ScriptError("Error parameter 2 'message' should be the identifier of a built-in or custom sting")

    langs = [0x7F]
    if error.msg.value in default_error_msg:
        custom_msg = False
        msg = default_error_msg[error.msg.value]
    else:
        custom_msg = True
        for translation in grf_strings[error.msg.value]:
            langs.append(translation['lang'])

    if error.data is not None:
        if not isinstance(error.data, Identifier):
            raise generic.ScriptError("Error parameter 3 'data' should be the identifier of a custom sting")
        for translation in grf_strings[error.data.value]:
            langs.append(translation['lang'])

    params = []
    for expr in error.params:
        if expr is None:
            params.append(None)
        elif isinstance(expr, Parameter) and isinstance(expr.num, ConstantNumeric):
            params.append(expr.num)
        else:
            tmp_param, tmp_param_actions = get_tmp_parameter(expr)
            action_list.extend(tmp_param_actions)
            params.append(ConstantNumeric(tmp_param))

    assert len(params) == 2

    langs = set(langs)
    for lang in langs:
        if custom_msg:
            msg = get_translation(error.msg.value, lang)
        data = None if error.data is None else get_translation(error.data.value, lang)
        if len(action6.modifications) > 0: action_list.append(action6)
        action_list.append(ActionB(severity, lang, msg, data, params[0], params[1]))

    free_parameters.extend([item for item in free_parameters_backup if not item in free_parameters])
    return action_list
