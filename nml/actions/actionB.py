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


class ActionB(base_action.BaseAction):
    def __init__(self, severity, lang, msg, data, extra_params):
        self.severity = severity
        self.lang = lang
        self.msg = msg
        self.data = data
        self.extra_params = extra_params

    def write(self, file):
        size = 4
        if not isinstance(self.msg, int):
            size += grfstrings.get_string_size(self.msg)
        if self.data is not None:
            size += grfstrings.get_string_size(self.data) + len(self.extra_params)

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
            for param in self.extra_params:
                param.write(file, 1)
        file.newline()
        file.end_sprite()

    def skip_action7(self):
        return False


default_error_msg = {
    "REQUIRES_TTDPATCH": 0,
    "REQUIRES_DOS_WINDOWS": 1,
    "USED_WITH": 2,
    "INVALID_PARAMETER": 3,
    "MUST_LOAD_BEFORE": 4,
    "MUST_LOAD_AFTER": 5,
    "REQUIRES_OPENTTD": 6,
}

error_severity = {
    "NOTICE": 0,
    "WARNING": 1,
    "ERROR": 2,
    "FATAL": 3,
}


def parse_error_block(error):
    action6.free_parameters.save()
    action_list = []
    act6 = action6.Action6()

    severity = actionD.write_action_value(error.severity, action_list, act6, 1, 1)[0]

    langs = [0x7F]
    if isinstance(error.msg, expression.String):
        custom_msg = True
        msg_string = error.msg
        grfstrings.validate_string(msg_string)
        langs.extend(grfstrings.get_translations(msg_string))
        for lang in langs:
            assert lang is not None
    else:
        custom_msg = False
        msg = error.msg.reduce_constant().value

    if error.data is not None:
        error.data = error.data.reduce()
        if isinstance(error.data, expression.String):
            grfstrings.validate_string(error.data)
            langs.extend(grfstrings.get_translations(error.data))
            for lang in langs:
                assert lang is not None
        elif not isinstance(error.data, expression.StringLiteral):
            raise generic.ScriptError(
                "Error parameter 3 'data' should be the identifier of a custom sting", error.data.pos
            )

    params = []
    for expr in error.params:
        if isinstance(expr, expression.Parameter) and isinstance(expr.num, expression.ConstantNumeric):
            params.append(expr.num)
        else:
            tmp_param, tmp_param_actions = actionD.get_tmp_parameter(expr)
            action_list.extend(tmp_param_actions)
            params.append(expression.ConstantNumeric(tmp_param))

    langs = list(set(langs))
    langs.sort()
    for lang in langs:
        if custom_msg:
            msg = grfstrings.get_translation(msg_string, lang)
        if error.data is None:
            data = None
        elif isinstance(error.data, expression.StringLiteral):
            data = error.data.value
        else:
            data = grfstrings.get_translation(error.data, lang)
        if len(act6.modifications) > 0:
            action_list.append(act6)
        action_list.append(ActionB(severity, lang, msg, data, params))

    action6.free_parameters.restore()
    return action_list
