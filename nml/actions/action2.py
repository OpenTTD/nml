from nml import generic
from nml.actions import base_action

free_action2_ids = range(1, 255)

action2_map = {}

class Action2(base_action.BaseAction):
    """
    Abstract Action2 base class.

    @ivar name; Name of the action2.
    @type name: C{str}

    @ivar feature: Action2 feature byte.
    @type feature: C{int}

    @ivar num_refs: Number of references to this action2.
    @type num_refs: C{int}

    @ivar id: Number of this action2.
    @type id: C{int}, or C{None} if no number is allocated yet.

    @ivar references: All Action2's that are references by this Action2.
    @type references: C{set}
    """
    def __init__(self, feature, name):
        global action2_map
        if name in action2_map:
            raise generic.ScriptError('Reusing names of switch/spritegroup blocks is not allowed, trying to use "%s"' % name)
        action2_map[name] = self

        self.feature = feature
        self.name = name
        self.num_refs = 0
        self.id = None
        self.references = set()

    def prepare_output(self):
        global free_action2_ids
        if self.num_refs == 0:
            self.id = free_action2_ids[0]
        else:
            self.id = free_action2_ids.pop()

    def write_sprite_start(self, file, size):
        file.comment("Name: " + self.name)
        file.start_sprite(size + 3)
        file.print_bytex(2)
        file.print_bytex(self.feature)
        file.print_bytex(self.id)

    def skip_action7(self):
        return False

    def skip_action9(self):
        return False

    def remove_tmp_location(self, location):
        """
        Recursively remove a location from the list of available temporary
        storage locations. It is not only removed from the the list of the
        current Action2Var but also from all Action2Var it calls.
        """
        if location not in self.tmp_locations: return
        self.tmp_locations.remove(location)
        for act2 in self.references:
            if isinstance(act2, Action2Var):
                act2.remove_tmp_location(location)

def add_ref(name, pos):
    global action2_map
    if name not in action2_map: raise generic.ScriptError("Referencing unknown action2 id: " + name, pos)
    action2_map[name].num_refs += 1
    return action2_map[name]

def remove_ref(name):
    if name == 'CB_FAILED': return 0
    global action2_map, free_action2_ids
    act2 = action2_map[name]
    id = act2.id
    act2.num_refs -= 1
    if act2.num_refs == 0: free_action2_ids.append(act2.id)
    return id

#list of sprite sets
spriteset_list = {}

def register_spriteset(spriteset):
    """
    Register a sprite set, so it can be resolved by name later

    @param spriteset: Spriteset to register
    @type spriteset: L{SpriteSet}
    """
    name = spriteset.name.value
    if name in spriteset_list:
        raise generic.ScriptError("Sprite set with name '%s' has already been defined" % name, spriteset.pos)
    spriteset_list[name] = spriteset

def resolve_spriteset(name):
    """
    Resolve a sprite set with a given name

    @param name: Name of the sprite set.
    @type name: L{Identifier}
    
    @return: The sprite set that the name refers to.
    """
    if name.value not in spriteset_list:
        raise generic.ScriptError("Referring to unknown spriteset '%s'" % name.value, name.pos)
    return spriteset_list[name.value]
