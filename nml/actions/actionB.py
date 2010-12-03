from nml import expression, generic, grfstrings
from nml.actions import base_action, action6, actionD

class ActionB(base_action.BaseAction):
    def __init__(self, severity, lang, msg, data, param1, param2):
        self.severity = severity
        self.lang = lang
        self.msg = msg
        self.data = data
        self.param1 = param1
        self.param2 = param2

    def write(self, file):
        size = 4
        if not isinstance(self.msg, int): size += grfstrings.get_string_size(self.msg)
        if self.data is not None:
            size += grfstrings.get_string_size(self.data)
            if self.param1 is not None:
                size += 1
                if self.param2 is not None:
                    size += 1

        file.start_sprite(size)
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
        file.end_sprite()

    def skip_action7(self):
        return False

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
    global default_error_msg
    action6.free_parameters.save()
    action_list = []
    act6 = action6.Action6()

    if isinstance(error.severity, expression.ConstantNumeric):
        severity = error.severity
    elif isinstance(error.severity, expression.Parameter) and isinstance(error.severity.num, expression.ConstantNumeric):
        act6.modify_bytes(error.severity.num.value, 1, 1)
        severity = expression.ConstantNumeric(0)
    else:
        tmp_param, tmp_param_actions = actionD.get_tmp_parameter(error.severity)
        action_list.extend(tmp_param_actions)
        act6.modify_bytes(tmp_param, 1, 1)
        severity = expression.ConstantNumeric(0)

    langs = [0x7F]
    if isinstance(error.msg, expression.String):
        custom_msg = True
        msg_string = error.msg
        langs.extend(grfstrings.get_translations(msg_string))
        for l in langs: assert l is not None
    else:
        custom_msg = False
        msg = error.msg.reduce_constant([default_error_msg]).value

    if error.data is not None:
        error.data = error.data.reduce()
        if isinstance(error.data, expression.String):
            if not grfstrings.is_valid_string(error.data.name.value):
                raise generic.ScriptError("Unknown string '%s'" % (error.data.name.value), error.data.pos)
            langs.extend(grfstrings.get_translations(error.data))
            for l in langs: assert l is not None
        elif not isinstance(error.data, expression.StringLiteral):
            raise generic.ScriptError("Error parameter 3 'data' should be the identifier of a custom sting", error.data.pos)

    params = []
    for expr in error.params:
        if expr is None:
            params.append(None)
        elif isinstance(expr, expression.Parameter) and isinstance(expr.num, expression.ConstantNumeric):
            params.append(expr.num)
        else:
            tmp_param, tmp_param_actions = actionD.get_tmp_parameter(expr)
            action_list.extend(tmp_param_actions)
            params.append(expression.ConstantNumeric(tmp_param))

    assert len(params) == 2

    langs = list(set(langs))
    langs.sort()
    for lang in langs:
        if custom_msg:
            msg = grfstrings.get_translation(msg_string.name.value, lang)
        if error.data is None:
            data = None
        elif isinstance(error.data, expression.StringLiteral):
            data = error.data.value
        else:
            data = grfstrings.get_translation(error.data.name.value, lang)
        if len(act6.modifications) > 0: action_list.append(act6)
        action_list.append(ActionB(severity, lang, msg, data, params[0], params[1]))

    action6.free_parameters.restore()
    return action_list
