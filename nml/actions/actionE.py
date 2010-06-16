from nml.expression import *
from action6 import *
from nml.actions import actionD

class ActionE(object):
    def __init__(self, grfid_list):
        self.grfid_list = [bswap32(grfid.value) for grfid in grfid_list]

    def prepare_output(self):
        pass

    def write(self, file):
        size = 2 + 4 * len(self.grfid_list)
        file.print_sprite_size(size)
        file.print_bytex(0x0E)
        file.print_byte(len(self.grfid_list))
        for grfid in self.grfid_list:
            file.newline()
            file.print_dwordx(grfid)
        file.newline()
        file.newline()

    def skip_action7(self):
        return True

    def skip_action9(self):
        return True

    def skip_needed(self):
        return True

def bswap32(value):
    return ((value & 0xFF) << 24) | ((value & 0xFF00) << 8) | ((value & 0xFF0000) >> 8) | ((value & 0xFF000000) >> 24)

def parse_deactivate_block(block):
    global free_parameters
    free_parameters_backup = free_parameters[:]
    grfid_list = []
    action_list = []
    act6 = Action6()
    offset = 2
    for grfid in block.grfid_list:
        if isinstance(grfid, ConstantNumeric):
            grfid_list.append(grfid)
        else:
            tmp_param, tmp_param_actions = actionD.get_tmp_parameter(grfid)
            action_list.extend(tmp_param_actions)
            for i in range(0, 4):
                if i == 0:
                    param = tmp_param
                else:
                    param = free_parameters.pop()
                    action_list.append(actionD.ActionD(ConstantNumeric(param), ConstantNumeric(tmp_param), actionD.ActionDOperator.SHFTU, ConstantNumeric(0xFF), ConstantNumeric(-8 * i)))
                act6.modify_bytes(param, 1, offset + 3 - i)
            grfid_list.append(ConstantNumeric(0))
        offset += 4

    if len(act6.modifications) != 0: action_list.append(act6)
    action_list.append(ActionE(grfid_list))

    free_parameters.extend([item for item in free_parameters_backup if not item in free_parameters])
    return action_list
