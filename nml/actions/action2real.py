from nml import generic
from nml.actions import action2

class Action2Real(action2.Action2):
    def __init__(self, feature, name, loaded_list, loading_list):
        action2.Action2.__init__(self, feature, name)
        self.loaded_list = loaded_list
        self.loading_list = loading_list

    def write(self, file):
        size = 2 + 2 * len(self.loaded_list) + 2 * len(self.loading_list)
        action2.Action2.write(self, file, size)
        file.print_byte(len(self.loaded_list))
        file.print_byte(len(self.loading_list))
        file.newline()
        for i in self.loaded_list:
            file.print_word(i)
        file.newline()
        for i in self.loading_list:
            file.print_word(i)
        file.newline()
        file.end_sprite()

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
        raise generic.ScriptError("Sprite groups that directly combine sprite sets are not supported for this feature: 0x" + generic.to_hex(feature, 2), spritegroup.pos)

    for view in spritegroup.spriteview_list:
        if view.name.value not in real_action2_alias: raise generic.ScriptError("Unknown sprite view type encountered in sprite group: " + view.name.value, view.pos)
        type, feature_list = real_action2_alias[view.name.value];
        #of course stations want to be different, their default view is the second type instead of the first
        if view.name.value == 'default' and feature is 0x04: type = 1
        if feature not in feature_list:
            raise generic.ScriptError("Sprite view type '" + view.name.value + "' is not supported for this feature: 0x" + generic.to_hex(feature, 2), view.pos)

        for set_name in view.spriteset_list:
            if set_name.value not in spritesets:
                raise generic.ScriptError("Unknown sprite set: " + set_name.value, set_name.pos)
            if type == 0: loaded_list.append(spritesets[set_name.value])
            else:  loading_list.append(spritesets[set_name.value])
    return [Action2Real(feature, spritegroup.name.value, loaded_list, loading_list)]
