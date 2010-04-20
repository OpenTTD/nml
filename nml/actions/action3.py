from nml.generic import *
from nml.expression import *
from action2 import *
from action6 import *
from actionD import *

class Action3:
    def __init__(self, feature, id):
        self.feature = feature
        self.id = id
        self.cid_mappings = []
    
    def write(self, file):
        file.write("0 03 ")
        print_bytex(file, self.feature)
        print_bytex(file, 1 if not self.is_livery_override else 0x81) # a single id
        print_varx(file, self.id, 3 if self.feature <= 3 else 1)
        print_byte(file, len(self.cid_mappings))
        file.write("\n")
        for cargo, cid in self.cid_mappings:
            cargo.write(file, 1)
            print_wordx(file, remove_ref(cid))
            file.write("\n")
        print_wordx(file, remove_ref(self.def_cid))
        file.write("\n\n")
    
    def skip_action7(self):
        return True
    
    def skip_action9(self):
        return No
    
    def skip_needed(self):
        return True

def parse_graphics_block(graphics_list, default_graphics, feature, id, is_livery_override = False):
    action_list = []
    action6 = Action6()
    if isinstance(id, ConstantNumeric):
        action3 = Action3(feature, id.value)
    else:
        tmp_param, tmp_param_actions = get_tmp_parameter(id)
        size = 3 if feature <= 3 else 1
        offset = 4 if feature <= 3 else 3
        action6.modify_bytes(tmp_param, size, offset)
        action_list.extend(tmp_param_actions)
        action3 = Action3(feature, 0)
    
    action3.is_livery_override = is_livery_override
    
    add_ref(default_graphics)
    action3.def_cid = default_graphics
    
    for graphics in graphics_list:
        add_ref(graphics.action2_id)
        cargo_id = reduce_constant(graphics.cargo_id, [cargo_numbers])
        action3.cid_mappings.append( (cargo_id, graphics.action2_id) )
    
    if len(action6.modifications) > 0: action_list.append(action6)
    action_list.append(action3)
    
    return action_list
