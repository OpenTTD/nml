import ast
from generic import *
from action6 import *
from actionD import *

class ActionE:
    def __init__(self, grfid_list):
        self.grfid_list = grfid_list
    
    def write(self, file):
        file.write("0 0E ")
        print_byte(file, len(self.grfid_list))
        for grfid in self.grfid_list:
            file.write("\n")
            print_dwordx(file, bswap32(grfid.value))
        file.write("\n\n")
    
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
    action6 = Action6()
    offset = 2
    for grfid in block.grfid_list:
        if isinstance(grfid, ast.ConstantNumeric):
            grfid_list.append(grfid)
        else:
            tmp_param, tmp_param_actions = get_tmp_parameter(grfid)
            action_list.extend(tmp_param_actions)
            for i in range(0, 4):
                if i == 0:
                    param = tmp_param
                else:
                    param = free_parameters.pop()
                    action_list.append(ActionD(ast.ConstantNumeric(param), ast.ConstantNumeric(tmp_param), ActionDOperator.SHFTU, ast.ConstantNumeric(0xFF), ast.ConstantNumeric(-8 * i)))
                action6.modify_bytes(param, 1, offset + 3 - i)
            grfid_list.append(ast.ConstantNumeric(0))
        offset += 4
    
    if len(action6.modifications) != 0: action_list.append(action6)
    action_list.append(ActionE(grfid_list))
    
    free_parameters.extend([item for item in free_parameters_backup if not item in free_parameters])
    return action_list
