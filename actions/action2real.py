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
        for i in self.loaded_list:
            print_word(file, i)
        for i in self.loading_list:
            print_word(file, i)
        file.write("\n")

real_action2_alias = {
    'loaded': 0,
    'loading': 1,
    'little': 0,
    'lots': 1,
    'default': 0,
}

def get_real_action2(spritegroup, feature, spritesets):
    global real_action2_alias
    loaded_list = []
    loading_list = []
    for view in spritegroup.spriteview_list:
        if view.name not in real_action2_alias: raise ScriptError("Unknown sprite view type encountered in sprite group: " + view.name)
        cur_list = loaded_list if real_action2_alias[view.name] == 0 else loading_list
        for set_name in view.spriteset_list:
            if set_name not in spritesets: raise ScriptError("Unknown sprite set: " + set_name)
            cur_list.append(spritesets[set_name])
    return Action2Real(feature, spritegroup.name, loaded_list, loading_list)
