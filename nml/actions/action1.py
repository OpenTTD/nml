from nml import generic
from nml.actions import action2, base_action, real_sprite

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

    if first_set.feature.value not in action2.features_sprite_set:
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

    #sprite sets should be 'flattened' for tile layouts
    flatten = first_set.feature.value in action2.features_sprite_layout

    real_sprite_list = []
    total_count = 0 #total number of sprites so far
    for i, item in enumerate(set_list):
        sprites = real_sprite.parse_sprite_list(item.sprite_list, item.pcx, block_name = item.name)
        for spritenum, sprite in enumerate(sprites):
            if sprite.label is not None:
                assert item.labels[sprite.label.value] is None
                item.labels[sprite.label.value] = spritenum
        real_sprite_list.extend(sprites)
        count = len(sprites)
        assert item.action1_num is None and item.action1_count is None
        item.action1_num = total_count if flatten else i
        item.action1_count = count
        total_count += count

    if len(set_list) != 0:
        if flatten:
            num_sets, num_ent = total_count, 1
        else:
            #check that all sprite sets have the same sprite count
            first_count = set_list[0].action1_count
            if any([item.action1_count != first_count for item in set_list]):
                #not all sprite sets have an equal length, this is an error
                #search for a sprite group to blame so we can show a nice message
                for g in group_list:
                    num = None
                    for s in g.referenced_nodes():
                        if num is None:
                            num = s.action1_count
                        elif num != s.action1_count:
                            raise generic.ScriptError("All sprite sets referred to by a sprite group should have the same number of sprites. Expected %d, got %d." % (num, s.action1_count), g.pos)
            num_sets, num_ent = len(set_list), first_count

        action_list.append(Action1(first_set.feature, num_sets, num_ent))
        action_list.extend(real_sprite_list)

    #add the sprite groups
    for g in group_list:
        action_list.extend(g.get_action_list())

    return action_list
