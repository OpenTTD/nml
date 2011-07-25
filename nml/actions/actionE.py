from nml import expression, nmlop
from nml.actions import base_action, action6, actionD

class ActionE(base_action.BaseAction):
    def __init__(self, grfid_list):
        self.grfid_list = grfid_list

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

def parse_deactivate_block(block):
    return [ActionE(block.grfid_list)]

