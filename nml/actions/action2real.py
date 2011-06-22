from nml import generic
from nml.actions import action2, action1

class Action2Real(action2.Action2):
    def __init__(self, feature, name, loaded_list, loading_list):
        action2.Action2.__init__(self, feature, name)
        self.loaded_list = loaded_list
        self.loading_list = loading_list

    def write(self, file):
        size = 2 + 2 * len(self.loaded_list) + 2 * len(self.loading_list)
        action2.Action2.write_sprite_start(self, file, size)
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
    'default': (0, [0x05, 0x0B, 0x0D, 0x10]), #canals, cargos, railtypes, airports
}

def get_real_action2s(spritegroup):
    global real_action2_alias
    loaded_list = []
    loading_list = []
    actions = []

    feature = spritegroup.feature.value
    if feature not in action2.features_sprite_group:
        raise generic.ScriptError("Sprite groups that combine sprite sets are not supported for feature '%02X'." % feature, spritegroup.pos)

    if len(spritegroup.spriteview_list) == 0:
        raise generic.ScriptError("Sprite groups require at least one sprite set.", spritegroup.pos)

    # First make sure that all referenced real sprites are put in a single action1
    all_spritesets = []
    for view in spritegroup.spriteview_list:
        all_spritesets.extend(action2.resolve_spritegroup(set_ref.name) for set_ref in view.spriteset_list)
    actions.extend(action1.add_to_action1(all_spritesets, feature, spritegroup.pos))

    for view in spritegroup.spriteview_list:
        if view.name.value not in real_action2_alias: raise generic.ScriptError("Unknown sprite view type encountered in sprite group: " + view.name.value, view.pos)
        type, feature_list = real_action2_alias[view.name.value]
        if feature not in feature_list:
            raise generic.ScriptError("Sprite view type '%s' is not supported for feature '%02X'." % (view.name.value, feature), view.pos)

        for set_ref in view.spriteset_list:
            spriteset = action2.resolve_spritegroup(set_ref.name)
            action1_index = action1.get_action1_index(spriteset)
            if type == 0: loaded_list.append(action1_index)
            else: loading_list.append(action1_index)

    actions.append(Action2Real(feature, spritegroup.name.value, loaded_list, loading_list))
    spritegroup.set_action2(actions[-1])
    return actions
