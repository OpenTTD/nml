from nml.generic import *
from real_sprite import *
from action2real import *
from action2layout import *

class ActionA(object):
    def __init__(self, num_sets, sets):
        self.num_sets = num_sets
        self.sets = sets

    def prepare_output(self):
        pass

    def write(self, file):
        #<Sprite-number> * <Length> 0A <num-sets> [<num-sprites> <first-sprite>]+
        size = 2 + 3 * len(self.sets)
        file.print_sprite_size(size)
        file.print_bytex(0x0A)
        file.print_byte(len(self.sets))
        for num, first in self.sets:
            file.print_byte(num)
            first.write(file, 2)
        file.newline()
        file.newline()

    def skip_action7(self):
        return True

    def skip_action9(self):
        return True

    def skip_needed(self):
        return True

def parse_actionA(replaces):
    action_list = []

    real_sprite_list = parse_sprite_list(replaces.sprite_list)

    action_list.append(ActionA(1, [(len(real_sprite_list), replaces.start_id)]))

    last_sprite = real_sprite_list[len(real_sprite_list) - 1][0]
    for sprite, id_dict in real_sprite_list:
        action_list.append(parse_real_sprite(sprite, replaces.pcx, sprite == last_sprite, id_dict))

    return action_list
