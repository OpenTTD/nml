from nml import generic, expression
from nml.actions import base_action, action2, action2real, action2layout, real_sprite

class Action1(base_action.BaseAction):
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

class SpriteSet(object):
    def __init__(self, param_list, sprite_list, pos):
        if not (1 <= len(param_list) <= 2):
            raise generic.ScriptError("Spriteset requires 1 or 2 parameters, encountered " + str(len(param_list)), pos)
        self.name = param_list[0]
        if not isinstance(self.name, expression.Identifier):
            raise generic.ScriptError("Spriteset parameter 1 'name' should be an identifier", self.name.pos)
        if len(param_list) >= 2:
            self.pcx = param_list[1].reduce()
            if not isinstance(self.pcx, expression.StringLiteral):
                raise generic.ScriptError("Spriteset-block parameter 2 'file' must be a string literal", self.pcx.pos)
        else:
            self.pcx = None
        self.sprite_list = sprite_list
        self.pos = pos
        self.feature = None #will be set during pre-processing
        self.referencing_groups = set() #sprite groups that reference this set
        self.action1_num = None #set number in action1

    def pre_process(self):
        action2.register_spritegroup(self)

    def debug_print(self, indentation):
        print indentation*' ' + 'Sprite set:', self.name.value
        print (indentation+2)*' ' + 'Source:  ', self.pcx.value if self.pcx is not None else 'None'
        print (indentation+2)*' ' + 'Sprites:'
        for sprite in self.sprite_list:
            sprite.debug_print(indentation + 4)

    def get_action_list(self):
        return parse_sprite_set(self) if self.action1_num is None else []

#to avoid circular imports, tell action2 about the existence of SpriteSet here
action2.spriteset_ref = SpriteSet

class SpriteGroup(object):
    def __init__(self, name, spriteview_list, pos = None):
        self.name = name
        self.spriteview_list = spriteview_list
        self.pos = pos
        self.feature = None #will be set during pre-processing
        self.referenced_sets = set()
        self.parsed = False

    def pre_process(self):
        assert self.feature is not None
        for spriteview in self.spriteview_list:
            self.referenced_sets.update(spriteview.check_spritesets(self))
        action2.register_spritegroup(self)

    def debug_print(self, indentation):
        print indentation*' ' + 'Sprite group:', self.name.value
        for spriteview in self.spriteview_list:
            spriteview.debug_print(indentation + 2)

    def get_action_list(self):
        actions = [] if self.parsed else action2real.get_real_action2s(self)
        self.parsed = True
        return actions

class LayoutSpriteGroup(object):
    def __init__(self, name, layout_sprite_list, pos = None):
        self.name = name
        self.layout_sprite_list = layout_sprite_list
        self.pos = pos
        self.feature = None #will be set during pre-processing
        self.referenced_sets = set()
        self.parsed = False

    def pre_process(self):
        assert self.feature is not None
        for layout_sprite in self.layout_sprite_list:
            self.referenced_sets.update(layout_sprite.check_spritesets(self))
        action2.register_spritegroup(self)

    def debug_print(self, indentation):
        print indentation*' ' + 'Tile layout sprite group:', self.name.value
        for layout_sprite in self.layout_sprite_list:
            layout_sprite.debug_print(indentation + 2)

    
    def get_action_list(self, only_action2 = False):
        actions = [] if self.parsed else action2layout.get_layout_action2s(self)
        self.parsed = True
        return actions

def parse_sprite_set(first_set):
    all_groups = set() #list of all groups
    all_sets = set([first_set]) #list of all sets
    handled_sets = set() #list of all sets that have already been handled
    action_list = []

    #compile a list of all groups and sets that will be handled in one go
    while 1:
        unhandled_sets = all_sets.difference(handled_sets)
        if len(unhandled_sets) == 0: break
        new_groups = set()
        for s in unhandled_sets:
            new_groups.update(s.referencing_groups)
        handled_sets.update(unhandled_sets)
        new_groups.difference_update(all_groups) #remove all elements already seen
        for g in new_groups:
            all_sets.update(g.referenced_sets)
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
                for s in g.referenced_sets:
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

#vehicles, stations, canals, cargos, airports, railtypes, houses, industry tiles, airport tiles, objects
action1_features = [0x00, 0x01, 0x02, 0x03, 0x04, 0x05, 0x0B, 0x0D, 0x10, 0x07, 0x09, 0x11, 0x0F]

def parse_sprite_block(sprite_block):
    global action1_features
    if sprite_block.feature.value not in action1_features:
        raise generic.ScriptError("Sprite blocks are not supported for this feature: 0x" + generic.to_hex(sprite_block.feature.value, 2), sprite_block.feature.pos)

    action_list = []
    for item in sprite_block.spriteset_list:
        action_list.extend(item.get_action_list())
    return action_list
