from nml.actions import base_action, real_sprite

class ActionA(base_action.BaseAction):
    def __init__(self, num_sets, sets):
        self.num_sets = num_sets
        self.sets = sets

    def write(self, file):
        #<Sprite-number> * <Length> 0A <num-sets> [<num-sprites> <first-sprite>]+
        size = 2 + 3 * len(self.sets)
        file.start_sprite(size)
        file.print_bytex(0x0A)
        file.print_byte(len(self.sets))
        for num, first in self.sets:
            file.print_byte(num)
            first.write(file, 2)
        file.newline()
        file.end_sprite()

def parse_actionA(replaces):
    real_sprite_list = real_sprite.parse_sprite_list(replaces.sprite_list, replaces.pcx)

    return [ActionA(1, [(len(real_sprite_list), replaces.start_id)])] + real_sprite_list
