from nml import expression, nmlop
from nml.actions import action6, actionD

class ActionE(object):
    def __init__(self, grfid_list):
        self.grfid_list = [bswap32(grfid.value) for grfid in grfid_list]

    def prepare_output(self):
        pass

    def write(self, file):
        size = 2 + 4 * len(self.grfid_list)
        file.start_sprite(size)
        file.print_bytex(0x0E)
        file.print_byte(len(self.grfid_list))
        for grfid in self.grfid_list:
            file.newline()
            file.print_dwordx(grfid)
        file.newline()
        file.end_sprite()

    def skip_action7(self):
        return True

    def skip_action9(self):
        return True

    def skip_needed(self):
        return True

def bswap32(value):
    return ((value & 0xFF) << 24) | ((value & 0xFF00) << 8) | ((value & 0xFF0000) >> 8) | ((value & 0xFF000000) >> 24)

def parse_deactivate_block(block):
    action6.free_parameters.save()
    grfid_list = []
    action_list = []
    act6 = action6.Action6()
    offset = 2
    for grfid in block.grfid_list:
        if isinstance(grfid, expression.ConstantNumeric):
            grfid_list.append(grfid)
        else:
            tmp_param, tmp_param_actions = actionD.get_tmp_parameter(grfid)
            action_list.extend(tmp_param_actions)
            for i in range(0, 4):
                if i == 0:
                    param = tmp_param
                else:
                    param = action6.free_parameters.pop()
                    action_list.append(actionD.ActionD(expression.ConstantNumeric(param), expression.ConstantNumeric(tmp_param),
                            nmlop.SHIFT_DU, expression.ConstantNumeric(0xFF), expression.ConstantNumeric(-8 * i)))
                act6.modify_bytes(param, 1, offset + 3 - i)
            grfid_list.append(expression.ConstantNumeric(0))
        offset += 4

    if len(act6.modifications) != 0: action_list.append(act6)
    action_list.append(ActionE(grfid_list))

    action6.free_parameters.restore()
    return action_list
