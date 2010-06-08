from nml.expression import *
from action2 import *
from action6 import *
from actionD import *

class Action3(object):
    def __init__(self, feature, id):
        self.feature = feature
        self.id = id
        self.cid_mappings = []

    def prepare_output(self):
        self.cid_mappings = [(cargo, remove_ref(cid)) for cargo, cid in self.cid_mappings]
        self.def_cid = remove_ref(self.def_cid)

    def write(self, file):
        size = 7 + 3 * len(self.cid_mappings)
        if self.feature <= 3: size += 2
        file.print_sprite_size(size)
        file.print_bytex(3)
        file.print_bytex(self.feature)
        file.print_bytex(1 if not self.is_livery_override else 0x81) # a single id
        file.print_varx(self.id, 3 if self.feature <= 3 else 1)
        file.print_byte(len(self.cid_mappings))
        file.newline()
        for cargo, cid in self.cid_mappings:
            cargo.write(file, 1)
            file.print_wordx(cid)
            file.newline()
        file.print_wordx(self.def_cid)
        file.newline()
        file.newline()

    def skip_action7(self):
        return True

    def skip_action9(self):
        return False

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

    add_ref(default_graphics.value)
    action3.def_cid = default_graphics.value

    for graphics in graphics_list:
        add_ref(graphics.action2_id.value)
        cargo_id = reduce_constant(graphics.cargo_id, [cargo_numbers])
        action3.cid_mappings.append( (cargo_id, graphics.action2_id.value) )

    if len(action6.modifications) > 0: action_list.append(action6)
    action_list.append(action3)

    return action_list
