from nml import generic
from nml.actions import base_action, real_sprite

class Action1(base_action.BaseAction):
    """
    Class representing an Action1

    @ivar feature: Feature of this action1
    @type feature: L{ConstantNumeric}

    @ivar num_sets: Number of (sprite) sets that follow this action 1.
    @type num_sets: C{int}

    @ivar num_ent: Number of sprites per set (e.g. (usually) 8 for vehicles)
    @type num_ent: C{int}
    """
    def __init__(self, feature, num_sets, num_ent):
        self.feature = feature
        self.num_sets = num_sets
        self.num_ent = num_ent

    def write(self, file):
        #<Sprite-number> * <Length> 01 <feature> <num-sets> <num-ent>
        file.start_sprite(6)
        file.print_bytex(1)
        self.feature.write(file, 1)
        file.print_byte(self.num_sets)
        file.print_varx(self.num_ent, 3)
        file.newline()
        file.end_sprite()

#vehicles, stations, canals, cargos, airports, railtypes, houses, industry tiles, airport tiles, objects
spriteset_features = [0x00, 0x01, 0x02, 0x03, 0x04, 0x05, 0x0B, 0x0D, 0x10, 0x07, 0x09, 0x11, 0x0F]

def parse_sprite_set(first_set):
    """
    Parse a sprite set into an action1
    Depending on the context, multiple action1s, action2s and real sprites will be generated.
    This is because all sprite sets that go into one sprite group need to be 'compiled' in one go.

    @param first_set: Sprite set to parse
    @type first_set: L{SpriteSet}

    @return: A list of generated actions
    @rtype: C{list} of L{BaseAction}
    """
    all_groups = set() #list of all groups
    all_sets = set([first_set]) #list of all sets
    handled_sets = set() #list of all sets that have already been handled
    action_list = []

    global spriteset_features
    if first_set.feature.value not in spriteset_features:
        raise generic.ScriptError("Sprite sets are not supported for this feature: " + generic.to_hex(first_set.feature.value, 2), first_set.feature.pos)

    #compile a list of all groups and sets that will be handled in one go
    while 1:
        unhandled_sets = all_sets.difference(handled_sets)
        if len(unhandled_sets) == 0: break
        new_groups = set()
        for s in unhandled_sets:
            new_groups.update(s.referencing_nodes())
        handled_sets.update(unhandled_sets)
        new_groups.difference_update(all_groups) #remove all elements already seen
        for g in new_groups:
            all_sets.update(g.referenced_nodes())
        all_groups.update(new_groups)

    #make a list of sprite sets to guarantee iteration order
    set_list = sorted(all_sets, key=lambda val: val.name.value)
    group_list = sorted(all_groups, key=lambda val: val.name.value)
    real_sprite_list = [real_sprite.parse_sprite_list(item.sprite_list, item.pcx, block_name = item.name) for item in set_list]

    if len(set_list) != 0:
        #check that all sprite sets have the same sprite count
        first_count = len(real_sprite_list[0])
        if any([len(sub) != first_count for sub in real_sprite_list]):
            #not all sprite sets have an equal length, this is an error
            #search for a sprite group to blame so we can show a nice message
            length_map = dict(map(None, set_list, [len(sub) for sub in real_sprite_list]))
            for g in group_list:
                num = None
                for s in g.referenced_nodes():
                    if num is None:
                        num = length_map[s]
                    elif num != length_map[s]:
                        raise generic.ScriptError("All sprite sets referred to by a sprite group should have the same number of sprites. Expected %d, got %d." % (num, length_map[s]), g.pos)

        #add an action1
        action_list.append(Action1(first_set.feature, len(set_list), first_count))
        #add the real sprites
        for sub in real_sprite_list:
            action_list.extend(sub)
        #set the sprite number for the sets
        for i, s in enumerate(set_list):
            assert s.action1_num == None
            s.action1_num = i

    #add the sprite groups
    for g in group_list:
        action_list.extend(g.get_action_list())

    return action_list
