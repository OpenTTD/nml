import ast
from action2 import *
from generic import *

class Action2Real(Action2):
    def __init__(self, feature, name, loaded_list, loading_list):
        Action2.__init__(self, feature, name)
        self.loaded_list = loaded_list
        self.loading_list = loading_list
        
    def write(self, file):
        Action2.write(self, file)
        print_byte(file, len(self.loaded_list))
        print_byte(file, len(self.loading_list))
        file.write("\n")
        for i in self.loaded_list:
            print_word(file, i)
        file.write("\n")
        for i in self.loading_list:
            print_word(file, i)
        file.write("\n\n")

real_action2_alias = {
    'loaded': (0, [0x00, 0x01, 0x02, 0x03]),  #vehicles
    'loading': (1, [0x00, 0x01, 0x02, 0x03]), #vehicles
    'little': (0, [0x04]), #stations
    'lots': (1, [0x04]),   #stations
    'default': (0, [0x04, 0x05, 0x0B, 0x0D, 0x10]), #vehicles, stations, canals, cargos, railtypes, airports
}

real_action2_features = [0x00, 0x01, 0x02, 0x03, 0x04, 0x05, 0x0B, 0x0D, 0x10] #vehicles, stations, canals, cargos, railtypes, airports

def get_real_action2s(spritegroup, feature, spritesets):
    global real_action2_alias, real_action2_features
    loaded_list = []
    loading_list = []
    
    if feature not in real_action2_features:
        raise ScriptError("Sprite groups that directly combine sprite sets are not supported for this feature: 0x" + to_hex(feature, 2))
    
    for view in spritegroup.spriteview_list:
        if view.name not in real_action2_alias: raise ScriptError("Unknown sprite view type encountered in sprite group: " + view.name)
        type, feature_list = real_action2_alias[view.name];
        #of course stations want to be different, their default view is the second type instead of the first
        if view.name == 'default' and feature is 0x04: type = 1
        if feature not in feature_list:
            raise ScriptError("Sprite view type '" + view.name + "' is not supported for this feature: 0x" + to_hex(feature, 2))
        
        for set_name in view.spriteset_list:
            if set_name not in spritesets:
                raise ScriptError("Unknown sprite set: " + set_name)
            if type == 0: loaded_list.append(spritesets[set_name])
            else:  loading_list.append(spritesets[set_name])
    return [Action2Real(feature, spritegroup.name, loaded_list, loading_list)]
