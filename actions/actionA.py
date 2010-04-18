import ast
from generic import *
from real_sprite import *
from action2real import *
from action2layout import *

class ActionA:
    def __init__(self, num_sets, sets):
        self.num_sets = num_sets
        self.sets = sets
    
    def write(self, file):
        #<Sprite-number> * <Length> 0A <num-sets> [<num-sprites> <first-sprite>]+
        file.write("-1 * 0 0A ")
        print_byte(file, len(self.sets))
        for num, first in self.sets:
            print_byte(file, num)
            first.write(file, 2)
        file.write("\n\n")
    
    def skip_action7(self):
        return True
    
    def skip_action9(self):
        return True
    
    def skip_needed(self):
        return True

def parse_actionA(replaces):
    action_list = []
    
    action_list.append(ActionA(1, [(len(replaces.sprite_list), replaces.start_id)]))
    
    last_sprite = replaces.sprite_list[len(replaces.sprite_list) - 1]
    for sprite in replaces.sprite_list:
        action_list.append(RealSpriteAction(sprite, replaces.pcx, sprite == last_sprite))
    
    return action_list
