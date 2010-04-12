import ast
from generic import *
from real_sprite import *
from action2real import *
from action2layout import *

class Action1:
    def __init__(self, feature, num_sets, num_ent):
        self.feature = feature
        self.num_sets = num_sets
        self.num_ent = num_ent
    
    def write(self, file):
        #<Sprite-number> * <Length> 01 <feature> <num-sets> <num-ent>
        file.write("-1 * 0 01 ")
        print_bytex(file, self.feature)
        print_byte(file, self.num_sets)
        print_byte(file, self.num_ent)
        file.write("\n")
    
    def skip_action7(self):
        return True
    
    def skip_action9(self):
        return True
    
    def skip_needed(self):
        return True

#vehicles, stations, canals, cargos, airports, railtypes, houses, industry tiles, airport tiles
action1_features = [0x00, 0x01, 0x02, 0x03, 0x04, 0x05, 0x0B, 0x0D, 0x10, 0x07, 0x09, 0x11]

def parse_sprite_block(sprite_block):
    global action1_features
    action_list = [None] #reserve one for action 1
    action_list_append = []
    spritesets = {} #map names to action1 entries
    num_sets = 0
    num_ent = -1
    
    if sprite_block.feature not in action1_features:
        raise ScriptError("Sprite blocks are not supported for this feature: " + str(sprite_block.feature))
    
    for item in sprite_block.spriteset_list:
        if isinstance(item, ast.SpriteSet):
            spritesets[item.name] = num_sets
            num_sets += 1
    
            if num_ent == -1:
                num_ent = len(item.sprite_list)
            elif num_ent != len(item.sprite_list):
                raise ScriptError("All sprite sets in a spriteblock should contain the same number of sprites. Expected " + str(num_ent) + ", got " + str(len(item.sprite_list)))
    
            for sprite in item.sprite_list:
                action_list.append(get_real_sprite(sprite, item.pcx))
    
        elif isinstance(item, ast.SpriteGroup):
            action_list_append.extend(get_real_action2s(item, sprite_block.feature, spritesets))
        else:
            assert isinstance(item, ast.LayoutSpriteGroup)
            action_list_append.extend(get_layout_action2s(item, sprite_block.feature, spritesets))
    
    action_list[0] = Action1(sprite_block.feature, num_sets, num_ent)
    action_list.extend(action_list_append)
    return action_list
